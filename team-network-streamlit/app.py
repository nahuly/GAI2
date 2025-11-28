import os, io, json, base64, re
import numpy as np
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
from openai import OpenAI
from matplotlib import font_manager  

# -----------------------------------------
# 🔐 OpenAI Client (이미지 생성 제외, 텍스트 기능만)
# -----------------------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# ---------------- 한글 폰트 설정 (NanumGothic) ----------------
FONT_PATH = os.path.join(os.path.dirname(__file__), "lib", "NanumGothic.ttf")

if os.path.exists(FONT_PATH):
    font_manager.fontManager.addfont(FONT_PATH)
    plt.rcParams["font.family"] = "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 깨짐 방지
else:
    # 로컬/클라우드에서 폰트가 없으면 경고만 띄우고 기본 폰트 사용
    st.warning(f"한글 폰트 파일을 찾을 수 없습니다: {FONT_PATH}")




# -----------------------------------------
# 📌 Streamlit 기본 설정
# -----------------------------------------
st.set_page_config(page_title="데이터분석랩 인적 네트워크", layout="wide")
st.title("🕸️ 데이터분석랩 인적 네트워크 v2")

st.markdown(
    """
팀 네트워크 분석 + MBTI 통계 + 포스터 뷰 + AI 분석 도구가 포함된 시각화 도구입니다.
"""
)

# ==========================================
# 🧩 Sidebar
# ==========================================
st.sidebar.header("⚙️ 시각화 설정")
physics = st.sidebar.selectbox("물리엔진", ["barnes_hut", "force_atlas_2based", "repulsion"], index=1)
base_node_size = st.sidebar.slider("기본 노드 크기", 5, 60, 16)
degree_scale = st.sidebar.slider("차수 기반 크기 스케일", 0, 40, 5)
show_labels = st.sidebar.checkbox("이름 라벨 표시", value=True)

# -----------------------------------------
# 🔎 MBTI 필터
# -----------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🔎 MBTI 필터")
ei_filter = st.sidebar.selectbox("E/I 필터", ["(전체)", "E만", "I만"], index=0)
tf_filter = st.sidebar.selectbox("T/F 필터", ["(전체)", "T만", "F만"], index=0)
mbti_exact_placeholder = st.sidebar.empty()

# -----------------------------------------
# 🧵 엣지 타입 토글
# -----------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🧵 엣지 타입 토글")

show_edge_all      = st.sidebar.checkbox("전체", value=False)

show_edge_dept     = st.sidebar.checkbox("소속", value=True)
show_edge_role     = st.sidebar.checkbox("직위", value=False)
show_edge_birth    = st.sidebar.checkbox("탄생년도", value=True)
show_edge_cohort   = st.sidebar.checkbox("동기", value=False)
show_edge_kakao    = st.sidebar.checkbox("카카오 분사", value=False)
show_edge_sex      = st.sidebar.checkbox("성별", value=False)
show_edge_joinyear = st.sidebar.checkbox("입사년도", value=False)
show_edge_mbti     = st.sidebar.checkbox("MBTI", value=True)
show_edge_blood    = st.sidebar.checkbox("혈액형", value=True)

# -----------------------------------------
# 검색 박스
# -----------------------------------------
st.sidebar.markdown("---")
search_box_placeholder = st.sidebar.empty()

# -----------------------------------------
# 데이터 업로드
# -----------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("📄 데이터 업로드")
uploaded_csv = st.sidebar.file_uploader("팀 CSV 업로드", type=["csv"])
uploaded_imgs = st.sidebar.file_uploader(
    "노드 사진 업로드 (여러 개 선택 가능)", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

# ==========================================
# 🧱 Default CSV
# ==========================================
default_csv = """이름,ldap,소속,직위,직군,탄생년도,입사년도,MBTI,혈액형,동기 여부,카카오분사,성별,워크샵 성향(2022),워크샵성향(2025),거주지,결혼여부,Image
김수형,cantabile.58,데이터분석랩,실장,개발,1970,2015,INTP,O,,카카오,남자,힐링,힐링,경기도,기혼,cantabile.png
김선영,party.92,BI셀,셀장,기술,1984,2016,ESFJ,A,,카카오,여자,힐링,힐링,경기도,기혼,party.png
송대섭,steven.song,BI셀,셀원,개발,1989,2018.1.22,ISTP,O,,,남자,힐링,힐링,경기도,미혼,steven.png
이나연,zoe.lee93,BI셀,셀원,개발,1993,2022.1.17,INFJ,A,,,여자,액티비티,힐링,서울,미혼,zoe.png
유선정,saylor.u,BI셀,셀원,기술,1994,2023.5.2,INFP,A,,,여자,,액티비티,경기도,미혼,saylor.png
조승민,noah.94,BI셀,셀원,기술,1994,2024.10.28,ESFJ,A,2024 경력직 동기,,남자,,액티비티,경기도,기혼,noah.png
김용환,feno.meno,BI셀,셀원,개발,1994,2024.11.18,INFP,AB,2024 경력직 동기,,남자,,액티비티,서울,미혼,feno.png
강동진,sonny.kang,BI셀,셀원,기술,1995,2021.6.23,ESFP,A,2021 인턴 동기,,남자,액티비티,액티비티,서울,미혼,sonny.png
조윤영,zoey.cho,BI셀,셀원,개발,1996,2021.6.23,INTJ,B,2021 인턴 동기,,여자,액티비티,힐링,서울,기혼,zoey.png
조은희,alysia.c,데이터테크셀,셀장,개발,1980,2017,ISTP,A,,카카오,여자,힐링,액티비티,서울,기혼,alysia.png
정동주,dj.jeong,데이터테크셀,셀원,개발,1988,2017.3.20,ISFP,AB,,,여자,힐링,액티비티,서울,기혼,dj.png
윤태식,levi.y,데이터테크셀,셀원,개발,1992,2020.12.22,ENTJ,B,,,남자,액티비티,액티비티,서울,기혼,levi.png
이창욱,carl.lee,데이터테크셀,셀원,개발,1993,2021.11.30,INTP,B,2021 공채 동기,,남자,힐링,액티비티,경기도,미혼,carl.png
김범준,breadly.abc,데이터테크셀,셀원,개발,1994,2024.11.18,ISFJ,O,2024 경력직 동기,,남자,,액티비티,서울,기혼,breadly.png
김희원,wonnie.kim,데이터테크셀,셀원,개발,1997,2021.6.23,ENFP,B,2021 인턴 동기,,여자,액티비티,힐링,서울,미혼,wonnie.png
박종범,jaybe.park,이상탐지셀,셀장,개발,1990,2019,ESTP,A,,,남자,액티비티,액티비티,서울,기혼,jaybe.png
주철민,iron.min,이상탐지셀,셀원,개발,1988,2018.9.18,INFJ,B,,,남자,힐링,힐링,경기도,미혼,iron.png
김우영,walt.kim,이상탐지셀,셀원,개발,1990,2020.11.24,,O,,,남자,액티비티,힐링,경기도,미혼,walt.png
이종우,justin.dev,이상탐지셀,셀원,개발,1995,2021.11.17,INTJ,B,2021 공채 동기,,남자,힐링,힐링,경기도,미혼,justin.png
김혜정,molly.ouo,이상탐지셀,셀원,개발,1999,2023.1.16,ENFJ,B,,,여자,,힐링,서울,미혼,molly.png
"""

# -----------------------------------------
# CSV 로드
# -----------------------------------------
if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
else:
    df = pd.read_csv(io.StringIO(default_csv))

df.columns = [c.strip() for c in df.columns]
if "Image" in df.columns and "image" not in df.columns:
    df["image"] = df["Image"]

df = df.map(lambda x: x.strip() if isinstance(x, str) else x)


# -----------------------------------------
# 이미지 저장 디렉토리
# -----------------------------------------
IMG_DIR = "node_images"
os.makedirs(IMG_DIR, exist_ok=True)

if uploaded_imgs:
    for f in uploaded_imgs:
        with open(os.path.join(IMG_DIR, f.name), "wb") as out:
            out.write(f.read())

# -----------------------------------------
# 이미지 파일 매칭 함수
# -----------------------------------------
def _variants(name: str):
    if not name:
        return []
    base, ext = os.path.splitext(str(name).strip())
    yield f"{base}{ext}"
    yield f"{base.lower()}{ext.lower()}"
    for e in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
        yield f"{base}{e}"
        yield f"{base.lower()}{e}"

MISSING_IMAGES = set()

def file_to_data_url(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{data}"

def resolve_image(row):
    img_col = str(row.get("image", "") or "").strip()
    ldap_val = str(row.get("ldap", "") or "").strip()

    # URL 또는 base64면 바로 사용
    if img_col.startswith(("http://", "https://", "data:")):
        return img_col

    candidates = []
    for v in _variants(img_col):
        candidates.append(os.path.join(IMG_DIR, v))

    if ldap_val:
        for ext in (".png", ".jpg", ".jpeg"):
            candidates.append(os.path.join(IMG_DIR, ldap_val + ext))
            candidates.append(os.path.join(IMG_DIR, ldap_val.lower() + ext))

    for path in candidates:
        if os.path.exists(path):
            return file_to_data_url(path)

    MISSING_IMAGES.add(f"{row.get('이름','?')} → {img_col}")
    return "https://via.placeholder.com/120?text=No+Image"


# ==========================================
# 📌 연도 정규화 (94 → 1994 처리)
# ==========================================
YEAR_RE = re.compile(r"(19|20)\d{2}")

def extract_year(v):
    if v is None:
        return None
    s = str(v)

    # 4자리 연도 먼저
    m = YEAR_RE.search(s)
    if m:
        try:
            return int(m.group())
        except:
            pass

    # 2자리 연도 (50 이상 = 1900대, 미만 = 2000대)
    m2 = re.search(r"(?<!\d)(\d{2})(?!\d)", s)
    if m2:
        yy = int(m2.group(1))
        return 1900 + yy if yy >= 50 else 2000 + yy
    return None

# 세대 구분용 헬퍼
def generation_from_year(y):
    if y is None or (isinstance(y, float) and np.isnan(y)):
        return None
    y = int(y)
    if y <= 1980:
        return "X세대"
    elif y <= 1996:
        return "밀레니얼"
    else:
        return "Z세대+"


df["탄생년도_Y"] = df["탄생년도"].apply(extract_year)
df["입사년도_Y"] = df["입사년도"].apply(extract_year)

# ==========================================
# 📌 MBTI 필터 옵션 만들기
# ==========================================
def mbti_list(series):
    vals = sorted([m for m in series.dropna().astype(str).unique() if m and m != "nan"])
    return ["(전체)"] + vals

mbti_exact = mbti_exact_placeholder.selectbox(
    "정확히 선택",
    mbti_list(df["MBTI"]),
    index=0,
    key="mbti_exact_sel",
)

# -----------------------------------------
# MBTI 필터링 함수
# -----------------------------------------
def keep_by_ei(m):
    if ei_filter == "(전체)" or not m:
        return True
    return (ei_filter == "E만" and str(m)[0] == "E") or (ei_filter == "I만" and str(m)[0] == "I")

def keep_by_tf(m):
    if tf_filter == "(전체)" or not m:
        return True
    return (tf_filter == "T만" and str(m)[2:3] == "T") or (tf_filter == "F만" and str(m)[2:3] == "F")

def keep_by_exact(m):
    return mbti_exact == "(전체)" or str(m) == mbti_exact

mask = df.apply(lambda r: keep_by_exact(r["MBTI"]) and keep_by_ei(r["MBTI"]) and keep_by_tf(r["MBTI"]), axis=1)

df_vis = df[mask].copy()
if df_vis.empty:
    st.warning("⚠️ 필터 조건에 맞는 데이터가 없습니다. 필터를 완화하세요.")
    df_vis = df.copy()

# ==========================================
# 📌 node_id 생성 (ldap 없으면 이름)
# ==========================================
def node_id_from_row(r):
    ldap_val = str(r.get("ldap", "")).strip()
    return ldap_val if ldap_val else str(r["이름"])

df["node_id"] = df.apply(node_id_from_row, axis=1)
df_vis["node_id"] = df_vis.apply(node_id_from_row, axis=1)

# ==========================================
# 🔍 검색 박스
# ==========================================
focus_node = ""
with search_box_placeholder.container():
    st.subheader("🔍 노드 검색")
    query = st.text_input("이름 또는 LDAP 검색", key="search_query_input")

    if query:
        cond = (
            df_vis["이름"].astype(str).str.contains(query, case=False, na=False)
            | df_vis["ldap"].astype(str).str.contains(query, case=False, na=False)
        )
        matches = df_vis[cond]

        if not matches.empty:
            opts = [f"{row['이름']} ({row['ldap']})" for _, row in matches.iterrows()]
            sel = st.selectbox("검색 결과", opts, key="search_result_box")

            # LDAP 선택
            if "(" in sel:
                chosen_ldap = sel.split("(")[-1][:-1]
                row = df[df["ldap"] == chosen_ldap].iloc[0]
                focus_node = row["node_id"]
        else:
            st.info("검색 결과가 없습니다.")

# ==========================================
# 🧩 유틸 함수: 값 존재 여부
# ==========================================
def is_filled(v):
    if v is None:
        return False
    s = str(v).strip()
    return s not in ("", "nan", "None", "null")

def valid_equal(a, b):
    if not is_filled(a) or not is_filled(b):
        return False
    return str(a).strip() == str(b).strip()

# ==========================================
# 🎨 MBTI 색상 규칙
# ==========================================
MBTI_COLORS = {
    "INFJ": "#6366f1",
    "INFP": "#22c55e",
    "INTJ": "#0ea5e9",
    "INTP": "#6366f1",
    "ISFP": "#22c55e",
    "ENFP": "#f97316",
    "ENFJ": "#ec4899",
    "ESFJ": "#eab308",
    "ESFP": "#a855f7",
}

def mbti_color(m):
    return MBTI_COLORS.get(str(m).strip(), "#9ca3af")

# ==========================================
# 🟧 카카오 분사 여부 판단 (입사전 회사 포함)
# ==========================================
def is_kakao_division(v):
    """입사전 회사 컬럼에 '카카오' 포함하면 카카오 분사 그룹"""
    if v is None:
        return False
    return "카카오" in str(v)


# ==========================================
# 🔗 비슷한 사람 TOP3 계산 (엣지 생성 조건과 100% 동일하게)
# ==========================================

similar_map = {}
rows_full = df.to_dict("records")

# 초기화
for r in rows_full:
    similar_map[r["node_id"]] = []

# ------------------------------------------
# 모든 사람 쌍 비교
# ------------------------------------------
for i in range(len(rows_full)):
    for j in range(i + 1, len(rows_full)):
        r1, r2 = rows_full[i], rows_full[j]
        nid1, nid2 = r1["node_id"], r2["node_id"]

        reasons = []

        # 소속
        if (show_edge_all or show_edge_dept) and valid_equal(r1["소속"], r2["소속"]):
            reasons.append("소속")

        # 직위
        if (show_edge_all or show_edge_role) and valid_equal(r1["직위"], r2["직위"]):
            reasons.append("직위")

        # 탄생년도
        if (show_edge_all or show_edge_birth) and valid_equal(
            extract_year(r1["탄생년도"]),
            extract_year(r2["탄생년도"]),
        ):
            reasons.append("탄생년도")

        # 동기
        if (show_edge_all or show_edge_cohort) and valid_equal(
            r1["동기 여부"], r2["동기 여부"]
        ):
            reasons.append("동기")

        # 카카오 분사 여부
        if (show_edge_all or show_edge_kakao):
            if is_kakao_division(r1["카카오분사"]) and is_kakao_division(r2["카카오분사"]):
                reasons.append("카카오 분사")

        # 성별
        if (show_edge_all or show_edge_sex) and valid_equal(r1["성별"], r2["성별"]):
            reasons.append("성별")

        # 입사년도
        if (show_edge_all or show_edge_joinyear) and valid_equal(
            extract_year(r1["입사년도"]),
            extract_year(r2["입사년도"]),
        ):
            reasons.append("입사년도")

        # MBTI
        if (show_edge_all or show_edge_mbti) and valid_equal(r1["MBTI"], r2["MBTI"]):
            reasons.append("MBTI")

        # 혈액형
        if (show_edge_all or show_edge_blood) and valid_equal(r1["혈액형"], r2["혈액형"]):
            reasons.append("혈액형")

        score = len(reasons)
        if score == 0:
            continue

        reason_text = ", ".join(reasons)

        similar_map[nid1].append({
            "name": r2["이름"],
            "ldap": r2["ldap"],
            "score": score,
            "reasons": reason_text,
        })
        similar_map[nid2].append({
            "name": r1["이름"],
            "ldap": r1["ldap"],
            "score": score,
            "reasons": reason_text,
        })

# TOP3만 남기기
for nid in similar_map:
    similar_map[nid].sort(key=lambda x: x["score"], reverse=True)
    similar_map[nid] = similar_map[nid][:3]


# ==========================================
# 🕸 Graph 생성 함수 (NetworkX 기반)
# ==========================================

def make_graph(df_people: pd.DataFrame):
    G = nx.Graph()

    # -------------------------------------
    # 노드 생성
    # -------------------------------------
    for _, r in df_people.iterrows():
        nid = r["node_id"]
        name = r["이름"]
        dept = r["소속"]
        img = resolve_image(r)

        title = "<br>".join([
            f"이름: {name}",
            f"ldap: {r['ldap']}",
            f"소속: {dept}",
            f"직위: {r['직위']}",
            f"직군: {r['직군']}",
            f"탄생년도: {extract_year(r['탄생년도'])}",
            f"입사년도: {extract_year(r['입사년도'])}",
            f"MBTI: {r['MBTI']}",
            f"혈액형: {r['혈액형']}",
            f"동기 여부: {r['동기 여부']}",
        ])

        border_color = mbti_color(r["MBTI"])

        node_kwargs = dict(
            title=title,
            group=dept,
            color={
                "border": border_color,
                "background": "#ffffff",
                "highlight": {"border": border_color, "background": "#ffffff"},
                "hover": {"border": border_color, "background": "#f9fafb"},
            },
        )

        if show_labels:
            node_kwargs["label"] = name
        if img:
            node_kwargs.update(shape="circularImage", image=img)

        G.add_node(nid, **node_kwargs)

    # -------------------------------------
    # 엣지 생성
    # -------------------------------------
    rows = df_people.to_dict("records")

    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            r1, r2 = rows[i], rows[j]
            reasons = []

            # 엣지 조건 - 유사도 계산과 동일하게
            if (show_edge_all or show_edge_dept) and valid_equal(r1["소속"], r2["소속"]):
                reasons.append(("소속", "같은 소속"))

            if (show_edge_all or show_edge_role) and valid_equal(r1["직위"], r2["직위"]):
                reasons.append(("직위", "같은 직위"))

            if (show_edge_all or show_edge_birth) and valid_equal(
                extract_year(r1["탄생년도"]),
                extract_year(r2["탄생년도"]),
            ):
                reasons.append(("탄생년도", "같은 탄생년도"))

            if (show_edge_all or show_edge_cohort) and valid_equal(
                r1["동기 여부"], r2["동기 여부"]
            ):
                reasons.append(("동기", "같은 동기"))

            if (show_edge_all or show_edge_kakao):
                if is_kakao_division(r1["카카오분사"]) and is_kakao_division(r2["카카오분사"]):
                    reasons.append(("카카오", "카카오 분사"))

            if (show_edge_all or show_edge_sex) and valid_equal(r1["성별"], r2["성별"]):
                reasons.append(("성별", "같은 성별"))

            if (show_edge_all or show_edge_joinyear) and valid_equal(
                extract_year(r1["입사년도"]),
                extract_year(r2["입사년도"]),
            ):
                reasons.append(("입사년도", "같은 입사년도"))

            if (show_edge_all or show_edge_mbti) and valid_equal(
                r1["MBTI"], r2["MBTI"]
            ):
                reasons.append(("MBTI", "같은 MBTI"))

            if (show_edge_all or show_edge_blood) and valid_equal(
                r1["혈액형"], r2["혈액형"]
            ):
                reasons.append(("혈액형", "같은 혈액형"))

            if len(reasons) == 0:
                continue

            weight = len(reasons)
            main_edge_type = reasons[0][0]
            labels = [lab for _, lab in reasons]

            title = " / ".join(labels) + f" (조건 {weight}개 일치)"

            G.add_edge(
                r1["node_id"], 
                r2["node_id"],
                weight=weight,
                title=title,
                edge_type=main_edge_type
            )

    return G


# ==========================================
# 🕸 실제 그래프 생성
# ==========================================
G = make_graph(df_vis)
deg = dict(G.degree())

# ==========================================
# 📊 네트워크 통계 (동일 소속 / MBTI / 동기 수)
# ==========================================
dept_map = df.set_index("node_id")["소속"].to_dict()
mbti_map = df.set_index("node_id")["MBTI"].to_dict()
cohort_map = df.set_index("node_id")["동기 여부"].to_dict()

stats = {}
for nid in G.nodes():
    dept = dept_map.get(nid)
    mbti = mbti_map.get(nid)
    cohort = cohort_map.get(nid)

    stats[nid] = {
        "degree": deg.get(nid, 0),
        "same_dept": sum(1 for v in dept_map.values() if v == dept) - 1 if dept else 0,
        "same_mbti": sum(1 for v in mbti_map.values() if v == mbti) - 1 if mbti else 0,
        "same_cohort": sum(1 for v in cohort_map.values() if v == cohort) - 1 if cohort else 0,
    }

# 노드 크기 결정
def sized(nid):
    row = df[df["node_id"] == nid].iloc[0]
    rank = row["직위"]
    base_rank = {"실장": 20, "셀장": 16, "셀원": 12}.get(rank, 12)
    return base_node_size + base_rank + degree_scale * deg.get(nid, 0)



# ==========================================
# 🖥 PyVis 네트워크 시각화
# ==========================================

net = Network(height="820px", width="100%", bgcolor="#ffffff", font_color="black")

# 물리 엔진 선택
if physics == "barnes_hut":
    net.barnes_hut()
elif physics == "force_atlas_2based":
    net.force_atlas_2based()
else:
    net.repulsion()

# ==========================================
# 📌 레이아웃 설정 (소속 = X축 / 동기 = Y축)
# ==========================================

depths = sorted(df_vis["소속"].dropna().unique())
depth_x = {d: i * 400 for i, d in enumerate(depths)}

cohorts = df_vis["동기 여부"].dropna().astype(str).str.strip()
cohort_vals = sorted([c for c in cohorts.unique() if c])
cohort_y = {c: idx * 250 for idx, c in enumerate(cohort_vals)}
cohort_y["(none)"] = len(cohort_vals) * 250

# ==========================================
# 🧩 노드 PyVis에 삽입
# ==========================================

for nid, data in G.nodes(data=True):
    row = df[df["node_id"] == nid].iloc[0]

    dept = str(row["소속"])
    cohort = str(row["동기 여부"]).strip()

    x = depth_x.get(dept, 0)
    y = cohort_y.get(cohort if cohort else "(none)", 0)

    net.add_node(
        nid,
        size=sized(nid),
        x=x,
        y=y,
        physics=True,
        **data
    )

# ==========================================
# 🎨 엣지 색상 규칙
# ==========================================

EDGE_COLORS = {
    "소속": "#22c55e",
    "직위": "#16a34a",
    "탄생년도": "#0ea5e9",
    "동기": "#3b82f6",
    "카카오": "#f59e0b",
    "성별": "#ec4899",
    "입사년도": "#a855f7",
    "MBTI": "#ef4444",
    "혈액형": "#f97316",
    "기타": "#9ca3af",
}

# ==========================================
# 🧵 엣지 삽입 (두께 = weight, 색상 = edge_type)
# ==========================================

for u, v, e in G.edges(data=True):
    edge_type = e.get("edge_type", "기타")
    color = EDGE_COLORS.get(edge_type, "#9ca3af")

    w = e.get("weight", 1)
    thickness = 1 + (w * 1.3)
    length = max(80, 280 - 40 * w)

    net.add_edge(
        u, v,
        value=thickness,
        color=color,
        title=e.get("title", ""),
        length=length,
    )

# ==========================================
# 🗂 HTML 생성
# ==========================================

html_file = "network.html"
net.save_graph(html_file)
with open(html_file, "r", encoding="utf-8") as f:
    html_src = f.read()

# ==========================================
# 🎛 클릭 시 상세 정보 패널 + 포커싱 기능 (JS)
# ==========================================

meta = {}
for _, r in df.iterrows():
    nid = r["node_id"]
    meta[nid] = {
        "이름": r["이름"],
        "ldap": r["ldap"],
        "소속": r["소속"],
        "직위": r["직위"],
        "직군": r["직군"],
        "입사년도": extract_year(r["입사년도"]),
        "MBTI": r["MBTI"],
        "혈액형": r["혈액형"],
        "동기 여부": r["동기 여부"],
        "연결 수": stats[nid]["degree"],
        "같은 소속 수": stats[nid]["same_dept"],
        "같은 MBTI 수": stats[nid]["same_mbti"],
        "같은 동기 수": stats[nid]["same_cohort"],
        "similar": similar_map.get(nid, []),
    }

focus_node_json = json.dumps(focus_node, ensure_ascii=False)

panel_js = f"""
<script>
window.nodeMeta = {json.dumps(meta, ensure_ascii=False)};

(function waitForNetwork() {{
  // 🔄 network 객체가 준비될 때까지 계속 재시도
  if (typeof network === 'undefined' || !network.body) {{
    setTimeout(waitForNetwork, 300);
    return;
  }}

  const panelId = 'profilePanel';
  let panel = document.getElementById(panelId);

  if (!panel) {{
    panel = document.createElement('div');
    panel.id = panelId;
    panel.style.position='fixed';
    panel.style.top='20px';
    panel.style.right='20px';
    panel.style.width='260px';
    panel.style.maxHeight='70vh';
    panel.style.overflow='auto';
    panel.style.border='1px solid #e5e7eb';
    panel.style.borderRadius='12px';
    panel.style.padding='10px';
    panel.style.background='rgba(255,255,255,0.93)';
    panel.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)';
    panel.style.fontSize='13px';
    panel.style.lineHeight='1.35';
    panel.innerHTML = '<b>노드를 클릭하면 상세 정보가 여기에 표시됩니다.</b><br><small>빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>';
    document.body.appendChild(panel);
  }}

  function showOnlyConnected(nid) {{
    const connectedNodes = network.getConnectedNodes(nid);
    connectedNodes.push(nid);

    const allNodeIds = network.body.data.nodes.getIds();
    const allEdgeIds = network.body.data.edges.getIds();

    // 노드 숨김/표시
    allNodeIds.forEach(function(id) {{
      const visible = connectedNodes.indexOf(id) !== -1;
      network.body.data.nodes.update({{ id: id, hidden: !visible }});
    }});

    // 엣지 숨김/표시
    const connectedEdges = network.getConnectedEdges(nid);
    allEdgeIds.forEach(function(id) {{
      const visible = connectedEdges.indexOf(id) !== -1;
      network.body.data.edges.update({{ id: id, hidden: !visible }});
    }});

    try {{
      network.focus(nid, {{ scale: 1.5, animation: true }});
    }} catch (e) {{}}
  }}

  function resetAll() {{
    const allNodeIds = network.body.data.nodes.getIds();
    const allEdgeIds = network.body.data.edges.getIds();

    allNodeIds.forEach(function(id) {{
      network.body.data.nodes.update({{ id: id, hidden: false }});
    }});
    allEdgeIds.forEach(function(id) {{
      network.body.data.edges.update({{ id: id, hidden: false }});
    }});

    network.fit();
  }}

  // 처음 검색해서 포커스할 노드가 있는 경우
  var initial = {focus_node_json};
  if (initial) {{
    setTimeout(function() {{
      try {{
        network.selectNodes([initial]);
        showOnlyConnected(initial);
      }} catch (e) {{}}
    }}, 600);
  }}

  // ✅ 클릭 핸들러 등록
  network.on("click", function(params) {{
    if (params.nodes && params.nodes.length > 0) {{
      var nid = params.nodes[0];
      var m = (window.nodeMeta || {{}})[nid] || {{}};
      var sims = m["similar"] || [];

      var simsHtml = "";
      if (sims.length > 0) {{
        simsHtml = "<hr><div><b>비슷한 사람 TOP3</b><ol style='padding-left:18px; margin:4px 0;'>";
        for (var i = 0; i < sims.length; i++) {{
          var s = sims[i];
          var label = (s.name || "") + (s.ldap ? " (" + s.ldap + ")" : "");
          var reasonTxt = s.reasons ? " - " + s.reasons + " 일치" : "";
          simsHtml += "<li>" + label + " (조건 " + (s.score || 0) + "개 일치" + reasonTxt + ")</li>";
        }}
        simsHtml += "</ol></div>";
      }}

      panel.innerHTML =
        "<h3 style='margin:0 0 6px 0;'>" + (m["이름"] || nid) + "</h3>" +
        "<div><b>ldap</b>: " + (m["ldap"] || "") + "</div>" +
        "<div><b>소속</b>: " + (m["소속"] || "") + "</div>" +
        "<div><b>직위</b>: " + (m["직위"] || "") + "</div>" +
        "<div><b>직군</b>: " + (m["직군"] || "") + "</div>" +
        "<div><b>입사년도</b>: " + (m["입사년도"] || "") + "</div>" +
        "<div><b>MBTI</b>: " + (m["MBTI"] || "") + "</div>" +
        "<div><b>혈액형</b>: " + (m["혈액형"] || "") + "</div>" +
        "<div><b>동기 여부</b>: " + (m["동기 여부"] || "") + "</div>" +
        "<hr>" +
        "<div><b>연결 수</b>: " + (m["연결 수"] || 0) + "</div>" +
        "<div><b>같은 소속 인원</b>: " + (m["같은 소속 수"] || 0) + "</div>" +
        "<div><b>같은 MBTI 인원</b>: " + (m["같은 MBTI 수"] || 0) + "</div>" +
        "<div><b>같은 동기 인원</b>: " + (m["같은 동기 수"] || 0) + "</div>" +
        simsHtml +
        "<hr><small>이 노드와 연결된 관계만 표시됩니다. 빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>";

      // 🔥 실제로 연결된 노드만 남기기
      showOnlyConnected(nid);

    }} else {{
      resetAll();
      panel.innerHTML =
        "<b>노드를 클릭하면 상세 정보가 여기에 표시됩니다.</b><br>" +
        "<small>빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>";
    }}
  }});
}})();
</script>
"""


# JS → HTML 삽입
html_src = html_src.replace("</body>", panel_js + "\n</body>")
# html(html_src, height=820, scrolling=True)

# ==========================================
# 🟩 엣지 색상 Legend (네트워크 위에 보여줌)
# ==========================================

legend_html = """
<div style="
    position:relative;
    top:0;
    padding:10px;
    margin-bottom:10px;
    background:#f3f4f6;
    border-radius:8px;
    font-size:13px;
    border:1px solid #e5e7eb;
">
<b>🎨 엣지 색상 의미</b><br>
소속 <span style='color:#22c55e;'>■■</span> /
직위 <span style='color:#16a34a;'>■■</span> /
탄생년도 <span style='color:#0ea5e9;'>■■</span> /
동기 <span style='color:#3b82f6;'>■■</span> /
카카오 <span style='color:#f59e0b;'>■■</span> /
성별 <span style='color:#ec4899;'>■■</span> /
입사년도 <span style='color:#a855f7;'>■■</span> /
MBTI <span style='color:#ef4444;'>■■</span> /
혈액형 <span style='color:#f97316;'>■■</span>
<br>
<small>선이 두꺼울수록 조건이 많이 겹칩니다.</small>
</div>
"""

st.markdown(legend_html, unsafe_allow_html=True)

# ==========================================
# 📡 네트워크 출력
# ==========================================

html(html_src, height=820, scrolling=True)

# 이미지 누락 표시
if MISSING_IMAGES:
    st.sidebar.markdown("### ❗ 누락된 이미지")
    for msg in sorted(MISSING_IMAGES):
        st.sidebar.write(msg)


# ==========================================
# 📊 Helper: bar chart with labels
# ==========================================

import matplotlib.pyplot as plt

def plot_bar_with_labels(data, title, xlabel="", ylabel="", color="#6366F1"):
    """
    data: pandas Series (index = label, values = 숫자)
    color: 막대 색 (기본 인디고)
    """
    fig, ax = plt.subplots()
    bars = ax.bar(data.index.astype(str), data.values, color=color)

    # 레이블 추가
    for bar in bars:
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            f"{yval:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.2, linestyle="--")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig



# ==========================================
# 📌 네트워크 중심성 분석 (Degree / Betweenness / Closeness / Eigenvector)
# ==========================================
with st.expander("📌 네트워크 중심성 분석 (Degree / Betweenness / Closeness / Eigenvector)"):
    if G.number_of_nodes() == 0:
        st.info("그래프에 노드가 없어 중심성을 계산할 수 없습니다.")
    else:
        # 중심성 계산
        degree_c = nx.degree_centrality(G)
        betweenness_c = nx.betweenness_centrality(G, normalized=True)
        closeness_c = nx.closeness_centrality(G)
        try:
            eigen_c = nx.eigenvector_centrality(G, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            eigen_c = {n: float("nan") for n in G.nodes()}

        rows = []
        for nid in G.nodes():
            row = df[df["node_id"] == nid].iloc[0]
            rows.append(
                {
                    "이름": row.get("이름", nid),
                    "소속": row.get("소속", ""),
                    "Degree": degree_c.get(nid, 0.0),
                    "Betweenness": betweenness_c.get(nid, 0.0),
                    "Closeness": closeness_c.get(nid, 0.0),
                    "Eigenvector": eigen_c.get(nid, 0.0),
                }
            )

        centrality_df = pd.DataFrame(rows).set_index("이름")

        st.markdown("**중심성 Top 5 (Eigenvector 기준)**")
        # 숫자 컬럼만 포맷 적용
        num_cols = ["Degree", "Betweenness", "Closeness", "Eigenvector"]

        top5 = centrality_df.sort_values("Eigenvector", ascending=False).head(5)
        top5_style = top5.style.format("{:.3f}", subset=num_cols)

        st.dataframe(top5_style)

        metric = st.selectbox(
            "시각화할 지표 선택",
            ["Degree", "Betweenness", "Closeness", "Eigenvector"],
            index=3,
        )

        fig_c = plot_bar_with_labels(
            centrality_df.sort_values(metric, ascending=False)[metric].head(15),
            f"{metric} 상위 15명",
            ylabel="값",
        )
        st.pyplot(fig_c)


# ==========================================
# 📊 MBTI & 입사년도 분포 + 전체 I/E, T/F 비율 + 소속별 MBTI 비율
# ==========================================

with st.expander("📊 MBTI / 입사년도 분포 차트"):
    col1, col2 = st.columns(2)

    # ---------------------------
    # ✅ 전체 MBTI 분포 (데이터분석랩 포함)
    # ---------------------------
    mbti_series = df["MBTI"].dropna().astype(str).str.strip()
    mbti_series = mbti_series[mbti_series != ""]
    if not mbti_series.empty:
        # 🔹 많이 나온 순으로 정렬
        mbti_counts = mbti_series.value_counts().sort_values(ascending=False)
        col1.markdown("**MBTI 분포**")
        fig = plot_bar_with_labels(
            mbti_counts,
            "MBTI 분포",
            ylabel="명",
            color="#6366F1",  # 인디고
        )
        col1.pyplot(fig)
    else:
        col1.info("MBTI 데이터가 없습니다.")

    # ---------------------------
    # ✅ 전체 입사년도 분포 (데이터분석랩 포함)
    # ---------------------------
    if "입사년도" in df.columns:
        years = df["입사년도"].apply(extract_year).dropna().astype(int)

        if not years.empty:
            year_counts = years.value_counts().sort_index()
            col2.markdown("**입사년도 분포 (정규화)**")
            fig2 = plot_bar_with_labels(
                year_counts,
                "입사년도 분포",
                ylabel="명",
                color="#22C55E",  # 초록
            )
            col2.pyplot(fig2)
        else:
            col2.info("입사년도 데이터가 없습니다.")
    else:
        col2.info("입사년도 컬럼이 없습니다.")

    # -----------------------------------------
    st.markdown("---")
    st.markdown("### 🌍 전체 MBTI I/E, T/F 비율 (파이차트) — *데이터분석랩 포함*")
    # -----------------------------------------

    overall_mbti = df["MBTI"].dropna().astype(str).str.strip()
    overall_mbti = overall_mbti[(overall_mbti != "") & (~overall_mbti.str.contains(r"\?"))]

    if not overall_mbti.empty:
        overall_IE = overall_mbti.str[0]
        overall_TF = overall_mbti.str[2]

        p1, p2 = st.columns(2)

        # 전체 I/E 비율
        ie_counts = overall_IE.value_counts()
        count_I = int(ie_counts.get("I", 0))
        count_E = int(ie_counts.get("E", 0))

        if count_I + count_E > 0:
            fig_ie, ax_ie = plt.subplots()
            ax_ie.pie(
                [count_I, count_E],
                labels=[f"I ({count_I})", f"E ({count_E})"],
                autopct="%1.1f%%",
                startangle=90,
            )
            ax_ie.axis("equal")
            p1.markdown("**전체 I/E 비율**")
            p1.pyplot(fig_ie)
        else:
            p1.info("I/E 비율을 계산할 수 있는 데이터가 없습니다.")

        # 전체 T/F 비율
        tf_counts = overall_TF.value_counts()
        count_T = int(tf_counts.get("T", 0))
        count_F = int(tf_counts.get("F", 0))

        if count_T + count_F > 0:
            fig_tf, ax_tf = plt.subplots()
            ax_tf.pie(
                [count_T, count_F],
                labels=[f"T ({count_T})", f"F ({count_F})"],
                autopct="%1.1f%%",
                startangle=90,
            )
            ax_tf.axis("equal")
            p2.markdown("**전체 T/F 비율**")
            p2.pyplot(fig_tf)
        else:
            p2.info("T/F 비율을 계산할 수 있는 데이터가 없습니다.")
    else:
        st.info("전체 MBTI 비율을 계산할 수 있는 유효한 MBTI 데이터가 없습니다.")

    # -----------------------------------------
    st.markdown("---")
    st.markdown("### 🧬 소속별 MBTI I/E, T/F 비율 (데이터분석랩 제외)")
    # -----------------------------------------

    if "MBTI" in df.columns and "소속" in df.columns:
        # MBTI + 소속 정제
        df_mbti = df[["소속", "MBTI"]].dropna().copy()
        df_mbti["MBTI"] = df_mbti["MBTI"].astype(str).str.strip()

        # 최소 3자, ? 포함된 애들은 제외 (I?T? 같은 값들)
        df_mbti = df_mbti[df_mbti["MBTI"].str.len() >= 3]
        df_mbti = df_mbti[~df_mbti["MBTI"].str.contains(r"\?")]

        # 🔴 여기에서만 데이터분석랩 제외
        df_mbti = df_mbti[df_mbti["소속"] != "데이터분석랩"]

        if not df_mbti.empty:
            df_mbti["IE"] = df_mbti["MBTI"].str[0]
            df_mbti["TF"] = df_mbti["MBTI"].str[2]

            col3, col4 = st.columns(2)

            # --- 소속별 I/E 비율 (% - I 비율 기준) ---
            ie_counts = df_mbti.groupby(["소속", "IE"]).size().unstack(fill_value=0)
            if "I" not in ie_counts.columns:
                ie_counts["I"] = 0
            if "E" not in ie_counts.columns:
                ie_counts["E"] = 0

            denom_ie = (ie_counts["I"] + ie_counts["E"]).replace(0, pd.NA)
            ie_ratio_I = (ie_counts["I"] / denom_ie).fillna(0) * 100

            col3.markdown("**소속별 I 비율 (%)**")
            fig3 = plot_bar_with_labels(ie_ratio_I, "소속별 I 비율 (%)", ylabel="%")
            col3.pyplot(fig3)

            # --- 소속별 T/F 비율 (% - T 비율 기준) ---
            tf_counts = df_mbti.groupby(["소속", "TF"]).size().unstack(fill_value=0)
            if "T" not in tf_counts.columns:
                tf_counts["T"] = 0
            if "F" not in tf_counts.columns:
                tf_counts["F"] = 0

            denom_tf = (tf_counts["T"] + tf_counts["F"]).replace(0, pd.NA)
            tf_ratio_T = (tf_counts["T"] / denom_tf).fillna(0) * 100

            col4.markdown("**소속별 T 비율 (%)**")
            fig4 = plot_bar_with_labels(tf_ratio_T, "소속별 T 비율 (%)", ylabel="%")
            col4.pyplot(fig4)
        else:
            st.info("소속별 MBTI 비율을 계산할 수 있는 데이터가 없습니다. (또는 모두 데이터분석랩이라 제외됨)")
    else:
        st.info("`소속` 또는 `MBTI` 컬럼이 없어 소속별 비율을 계산할 수 없습니다.")

# ==========================================
# 🧬 MBTI 요소 비율 막대형 히트맵
# ==========================================
with st.expander("🧬 MBTI 요소 비율 히트맵 (막대형)"):
    mbti_clean = df["MBTI"].dropna().astype(str).str.strip()
    mbti_clean = mbti_clean[
        (mbti_clean != "") & (~mbti_clean.str.contains(r"\?")) & (mbti_clean.str.len() >= 4)
    ]

    if mbti_clean.empty:
        st.info("유효한 MBTI 데이터가 없습니다.")
    else:
        pairs = {
            "I/E": ("I", "E", mbti_clean.str[0]),
            "N/S": ("N", "S", mbti_clean.str[1]),
            "T/F": ("T", "F", mbti_clean.str[2]),
            "J/P": ("J", "P", mbti_clean.str[3]),
        }

        fig, ax = plt.subplots(figsize=(8, 6))
        y_labels = []
        left_bars = []
        right_bars = []
        left_labels = []
        right_labels = []

        for idx, (label, (left_key, right_key, series)) in enumerate(pairs.items()):
            counts = series.value_counts()
            total = counts.get(left_key, 0) + counts.get(right_key, 0)
            if total == 0:
                left_pct, right_pct = 0, 0
            else:
                left_pct = counts.get(left_key, 0) / total * 100
                right_pct = counts.get(right_key, 0) / total * 100

            y_labels.append(label)
            left_bars.append(left_pct)
            right_bars.append(right_pct)
            left_labels.append(f"{left_pct:.1f}%")
            right_labels.append(f"{right_pct:.1f}%")

        y_pos = np.arange(len(y_labels))

        # 왼쪽 바 (첫 글자)
        ax.barh(y_pos, left_bars, color="#4ade80", label="첫 글자")  # 초록 계열
        # 오른쪽 바 (둘째 글자)
        ax.barh(y_pos, right_bars, left=left_bars, color="#60a5fa", label="둘째 글자")  # 파랑 계열

        # 라벨(수치) 표시
        for i in range(len(y_labels)):
            ax.text(left_bars[i] / 2, i, left_labels[i], va="center", ha="center", color="black")
            ax.text(left_bars[i] + right_bars[i] / 2, i, right_labels[i], va="center", ha="center", color="black")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(y_labels)
        ax.set_xlabel("비율 (%)")
        ax.set_title("MBTI 요소 비율 막대형 히트맵")

        ax.legend(loc="lower right")
        plt.tight_layout()
        st.pyplot(fig)



# ==========================================
# 🌈 소속별 MBTI 다양성 지수 (Shannon entropy)
# ==========================================
with st.expander("🌈 소속별 MBTI 다양성 지수"):
    if "소속" not in df.columns or "MBTI" not in df.columns:
        st.info("`소속` 또는 `MBTI` 컬럼이 없어 다양성 지수를 계산할 수 없습니다.")
    else:
        tmp = df[["소속", "MBTI"]].dropna().copy()
        tmp["MBTI"] = tmp["MBTI"].astype(str).str.strip()
        tmp = tmp[
            (tmp["MBTI"] != "") & (~tmp["MBTI"].str.contains(r"\?")) & (tmp["MBTI"].str.len() >= 4)
        ]

        # 🔴 데이터분석랩 제외
        tmp = tmp[tmp["소속"] != "데이터분석랩"]

        if tmp.empty:
            st.info("유효한 MBTI 데이터가 없어 다양성 지수를 계산할 수 없습니다.")
        else:
            def shannon_entropy(series: pd.Series) -> float:
                counts = series.value_counts()
                p = counts / counts.sum()
                return float(-(p * np.log2(p)).sum())

            diversity = tmp.groupby("소속")["MBTI"].apply(shannon_entropy)

            st.markdown("값이 클수록 MBTI 구성이 다양한 팀입니다. (데이터분석랩 제외)")
            fig_div = plot_bar_with_labels(
                diversity.sort_values(ascending=False),
                "소속별 MBTI 다양성 지수 (Shannon entropy)",
                ylabel="Entropy",
                color="#0EA5E9",  # 하늘색
            )
            st.pyplot(fig_div)


# ==========================================
# 👶 세대 구성 그래프
# ==========================================
with st.expander("👶 세대 구성 그래프"):
    if "탄생년도_Y" not in df.columns:
        st.info("정규화된 탄생년도(`탄생년도_Y`)가 없어 세대 구성을 계산할 수 없습니다.")
    else:
        gen_series = df["탄생년도_Y"].apply(generation_from_year)
        gen_series = gen_series.dropna()

        if gen_series.empty:
            st.info("세대 정보를 계산할 수 있는 데이터가 없습니다.")
        else:
            # 전체 세대 분포
            counts = gen_series.value_counts()
            fig_g, ax_g = plt.subplots()
            ax_g.pie(
                counts.values,
                labels=[f"{k} ({v})" for k, v in counts.items()],
                autopct="%1.1f%%",
                startangle=90,
            )
            ax_g.axis("equal")
            st.markdown("**전체 세대 분포**")
            st.pyplot(fig_g)

            # 소속별 세대 분포 (비율)  👉 데이터분석랩 제외
            if "소속" in df.columns:
                tmp = pd.DataFrame({"소속": df["소속"], "세대": gen_series}).dropna()

                # 🔴 데이터분석랩 제외
                tmp = tmp[tmp["소속"] != "데이터분석랩"]

                if not tmp.empty:
                    pivot = (
                        tmp.groupby(["소속", "세대"]).size().unstack(fill_value=0)
                    )
                    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

                    st.markdown("**소속별 세대 비율 (%) (데이터분석랩 제외)**")
                    fig_g2, ax_g2 = plt.subplots()
                    bottom = np.zeros(len(pivot_pct))
                    x = np.arange(len(pivot_pct.index))

                    for gen in pivot_pct.columns:
                        vals = pivot_pct[gen].values
                        ax_g2.bar(x, vals, bottom=bottom, label=gen)
                        bottom += vals

                    ax_g2.set_xticks(x)
                    ax_g2.set_xticklabels(pivot_pct.index, rotation=45, ha="right")
                    ax_g2.set_ylabel("%")
                    ax_g2.set_title("소속별 세대 비율 (Stacked)")
                    ax_g2.legend(title="세대")
                    plt.tight_layout()
                    st.pyplot(fig_g2)
                else:
                    st.info("데이터분석랩을 제외하고는 세대 비율을 계산할 수 있는 데이터가 없습니다.")



# ==========================================
# 🤝 팀 케미 분석 (similar_map 기반)
# ==========================================
with st.expander("🤝 팀 케미 분석"):
    # ldap -> node_id 매핑
    ldap_to_nid = {}
    for _, r in df.iterrows():
        ldap_val = str(r.get("ldap", "") or "").strip()
        if ldap_val:
            ldap_to_nid[ldap_val] = r["node_id"]

    pair_dict = {}
    for nid, lst in similar_map.items():
        for s in lst:
            other_ldap = str(s.get("ldap", "") or "").strip()
            other_nid = ldap_to_nid.get(other_ldap)
            if not other_nid:
                continue
            key = tuple(sorted([nid, other_nid]))
            cur = pair_dict.get(key)
            if (cur is None) or (s["score"] > cur["score"]):
                pair_dict[key] = {
                    "A_id": key[0],
                    "B_id": key[1],
                    "score": s["score"],
                    "reasons": s.get("reasons", ""),
                }

    if not pair_dict:
        st.info("현재 설정된 엣지 기준으로 케미를 계산할 수 있는 쌍이 없습니다.")
    else:
        rows = []
        for key, val in pair_dict.items():
            a_row = df[df["node_id"] == val["A_id"]].iloc[0]
            b_row = df[df["node_id"] == val["B_id"]].iloc[0]
            rows.append(
                {
                    "A": f"{a_row.get('이름', '')} ({a_row.get('ldap', '')})",
                    "B": f"{b_row.get('이름', '')} ({b_row.get('ldap', '')})",
                    "케미 점수(조건 수)": int(val["score"]),
                    "공통 조건": val["reasons"],
                }
            )

        pair_df = pd.DataFrame(rows).sort_values(
            "케미 점수(조건 수)", ascending=False
        )

        st.markdown("**케미 상위 TOP 10 쌍**")
        st.dataframe(pair_df.head(10))

        avg_score = pair_df["케미 점수(조건 수)"].mean()
        max_score = pair_df["케미 점수(조건 수)"].max()
        st.markdown(
            f"- 전체 평균 케미 점수: **{avg_score:.2f}**  (최대 {max_score} 조건 일치)\n"
            f"- 총 케미 쌍 수: **{len(pair_df)}**"
        )

        # 케미 점수 분포
        fig_k = plot_bar_with_labels(
            pair_df["케미 점수(조건 수)"].value_counts().sort_index(),
            "케미 점수 분포 (조건 일치 개수)",
            ylabel="쌍 수",
        )
        st.pyplot(fig_k)



# ==========================================
# 🖼 포스터 뷰 (팀 구성도 인쇄용 레이아웃)
# ==========================================

with st.expander("🖼 팀 구성도 포스터 뷰 (소속별 정렬)"):
    st.markdown("PDF로 저장하면 포스터처럼 사용할 수 있어요!")

    # 원하는 소속 순서
    dept_order = ["데이터분석랩", "BI셀", "데이터테크셀", "이상탐지셀"]

    # 소속별 그룹
    grouped = df.groupby("소속")

    # 1) 우리가 지정한 순서대로 먼저 출력
    for dept in dept_order:
        if dept not in grouped.groups:
            continue  # 해당 소속이 없으면 건너뛰기

        group = grouped.get_group(dept)
        st.markdown(f"## 📌 {dept}")
        cols = st.columns(4)

        for idx, (_, r) in enumerate(group.iterrows()):
            col = cols[idx % 4]
            img = resolve_image(r)

            if img:
                col.image(img, width=120)

            jy = extract_year(r.get("입사년도"))
            col.markdown(
                f"**{r.get('이름','')}**  \n"
                f"{r.get('직위','')}  \n"
                f"{jy or ''} 입사 · {r.get('MBTI','')}"
            )

    # 2) 만약 다른 소속이 더 있다면, 나머지는 이름순/사전순으로 뒤에 출력
    other_depts = [d for d in grouped.groups.keys() if d not in dept_order]

    for dept in sorted(other_depts):
        group = grouped.get_group(dept)
        st.markdown(f"## 📌 {dept}")
        cols = st.columns(4)

        for idx, (_, r) in enumerate(group.iterrows()):
            col = cols[idx % 4]
            img = resolve_image(r)

            if img:
                col.image(img, width=120)

            jy = extract_year(r.get("입사년도"))
            col.markdown(
                f"**{r.get('이름','')}**  \n"
                f"{r.get('직위','')}  \n"
                f"{jy or ''} 입사 · {r.get('MBTI','')}"
            )


# ==========================================
# 📑 데이터 미리보기
# ==========================================

with st.expander("📑 데이터 미리보기 (필터 적용)"):
    st.dataframe(df_vis)



# ==========================================
# 🤖 AI 기능 5종 (OpenAI 텍스트 모델 사용)
# ==========================================

# ------------------------------------------
# 1) 팀 네트워크 분석 요약
# ------------------------------------------
def ai_team_network_summary(G, df):
    summary_prompt = f"""
You are an expert organization analyst.

Analyze the following team network:

- Nodes: {len(G.nodes())}
- Edges: {len(G.edges())}
- Top degrees: {sorted([(n, d) for n, d in G.degree()], key=lambda x: -x[1])[:5]}

Also analyze:
- MBTI distribution
- Department composition
- Cross-department connection patterns

Return:
1) 네트워크 기반 조직 분석
2) 팀 분위기/구조 특징
3) 개선 제안 3가지
4) 매력 포인트 3가지
"""

    resp = client.responses.create(
        model="gpt-4.1",
        input=summary_prompt
    )
    return resp.output_text


# ------------------------------------------
# 2) 개인 프로필 강화 설명
# ------------------------------------------
def ai_rich_profile(row, similar_top3):
    prompt = f"""
You are generating a rich personality profile of the following team member:

이름: {row['이름']}
소속: {row['소속']}
직위: {row['직위']}
입사년도: {extract_year(row['입사년도'])}
MBTI: {row['MBTI']}
혈액형: {row['혈액형']}
동기 여부: {row['동기 여부']}
성별: {row['성별']}

비슷한 사람 TOP3:
{json.dumps(similar_top3, ensure_ascii=False)}

Write:
1) 이 사람의 분위기/업무 스타일/장점
2) MBTI 기반 해석
3) 팀 내 역할과 강점
4) TOP3 similarity 기반 인간관계 분석
5) 마지막에 한 줄 별명 추천
"""

    resp = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )
    return resp.output_text


# ------------------------------------------
# 3) 팀원 간 궁합 분석
# ------------------------------------------
def ai_chemistry(a_row, b_row):
    prompt = f"""
두 팀원의 궁합을 분석해주세요.

A:
- 이름: {a_row['이름']}
- 소속: {a_row['소속']}
- 직위: {a_row['직위']}
- MBTI: {a_row['MBTI']}

B:
- 이름: {b_row['이름']}
- 소속: {b_row['소속']}
- 직위: {b_row['직위']}
- MBTI: {b_row['MBTI']}

Return:
1) 전체 케미 점수 (10점 기준)
2) 잘 맞는 이유
3) 부딪힐 수 있는 부분
4) 협업 시 팁 3가지
5) 해석 스타일은 “프로 리더의 관찰일지” 느낌
"""

    resp = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )
    return resp.output_text


# ------------------------------------------
# 4) 팀 슬로건 생성
# ------------------------------------------
def ai_team_slogans(df):
    members = ", ".join(df["이름"].tolist())

    prompt = f"""
팀 구성원: {members}

데이터분석랩 & 각 셀(BI셀, 데이터테크셀, 이상탐지셀)의 팀 슬로건을 만들어주세요.

슬로건 종류:
1) 감성 버전
2) 유머 버전
3) 히어로 영화 포스터 버전
4) 짧고 간결한 캐치프레이즈 5개
"""

    resp = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )
    return resp.output_text


# ------------------------------------------
# 5) 아이처럼 설명한 셀 소개
# ------------------------------------------
def ai_childlike_cell_intro(df):
    dept_groups = df.groupby("소속").size().to_dict()

    prompt = f"""
각 셀 구성 인원 수:
{json.dumps(dept_groups, ensure_ascii=False)}

각 셀을 "5살 어린이에게 설명하듯이" 귀엽고 단순하게 소개해줘.
각 셀마다:
- 어떤 역할을 하는 곳인지
- 어떤 사람들이 있는지
- 동물로 비유하면 어떤 느낌인지
"""

    resp = client.responses.create(
        model="gpt-4.1",
        input=prompt,
    )
    return resp.output_text


# ==========================================
# 🎛 AI 분석 도구 UI (메인 페이지 아래)
# ==========================================

st.markdown("---")
st.header("🔮 AI 분석 도구")

ai_tabs = st.tabs([
    "📡 팀 네트워크 분석",
    "🧠 개인 프로필 AI 해석",
    "💞 팀원 궁합 분석",
    "⚡ 팀 슬로건 생성",
    "👶 아이처럼 설명한 셀 소개"
])


# ------------------------------------------
# 📡 1) 팀 네트워크 분석 요약
# ------------------------------------------
with ai_tabs[0]:
    st.subheader("📡 팀 네트워크 분석 요약")

    if st.button("AI 분석 생성", key="btn_net_summary"):
        with st.spinner("AI가 팀 네트워크를 분석하는 중..."):
            try:
                summary = ai_team_network_summary(G, df)
                st.markdown(summary)
            except Exception as e:
                st.error(f"오류 발생: {e}")


# ------------------------------------------
# 🧠 2) 개인 프로필 AI 해석
# ------------------------------------------
with ai_tabs[1]:
    st.subheader("🧠 개인 프로필 AI 해석")

    target = st.selectbox("팀원 선택", df["이름"].unique(), key="profile_select")

    if st.button("AI 프로필 생성", key="btn_profile"):
        row = df[df["이름"] == target].iloc[0]
        nid = row["node_id"]
        similar3 = similar_map.get(nid, [])

        with st.spinner("AI가 프로필을 생성하는 중..."):
            try:
                profile = ai_rich_profile(row, similar3)
                st.markdown(profile)
            except Exception as e:
                st.error(f"오류 발생: {e}")


# ------------------------------------------
# 💞 3) 팀원 궁합 분석
# ------------------------------------------
with ai_tabs[2]:
    st.subheader("💞 팀원 간 궁합 분석")

    colA, colB = st.columns(2)
    name_a = colA.selectbox("A 팀원", df["이름"].unique(), key="chem_a")
    name_b = colB.selectbox("B 팀원", df["이름"].unique(), key="chem_b")

    if st.button("궁합 분석하기", key="btn_chem"):
        if name_a == name_b:
            st.warning("서로 다른 팀원을 선택해주세요!")
        else:
            a_row = df[df["이름"] == name_a].iloc[0]
            b_row = df[df["이름"] == name_b].iloc[0]

            with st.spinner("AI가 궁합 분석 중..."):
                try:
                    result = ai_chemistry(a_row, b_row)
                    st.markdown(result)
                except Exception as e:
                    st.error(f"오류 발생: {e}")


# ------------------------------------------
# ⚡ 4) 팀 슬로건 생성
# ------------------------------------------
with ai_tabs[3]:
    st.subheader("⚡ 팀 슬로건 만들기")

    if st.button("슬로건 자동 생성", key="btn_slogan"):
        with st.spinner("AI가 슬로건을 생성하는 중..."):
            try:
                result = ai_team_slogans(df)
                st.markdown(result)
            except Exception as e:
                st.error(f"오류 발생: {e}")


# ------------------------------------------
# 👶 5) 아이처럼 설명한 셀 소개
# ------------------------------------------
with ai_tabs[4]:
    st.subheader("👶 아이처럼 설명한 셀 소개")

    if st.button("셀 소개 생성하기", key="btn_childlike"):
        with st.spinner("AI가 귀여운 설명 생성 중..."):
            try:
                result = ai_childlike_cell_intro(df)
                st.markdown(result)
            except Exception as e:
                st.error(f"오류 발생: {e}")
