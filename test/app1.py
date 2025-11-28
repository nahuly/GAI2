# app.py (Streamlit + PyVis)
# 우리팀 인적 네트워크 — 업데이트: 이미지 매칭/연도 파싱/필터/진단 개선
#
# 실행:
#   streamlit run app.py
#
# 의존성:
#   pip install streamlit pyvis networkx pandas matplotlib

import os, io, json, base64, re
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
from openai import OpenAI
import os

# Streamlit secrets에 저장했다는 가정 (또는 환경변수 쓰면 그걸로 바꿔도 OK)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# 환경변수라면 이렇게:
# openai.api_key = os.environ.get("OPENAI_API_KEY", "")

# ---------------- 기본 설정 ----------------
st.set_page_config(page_title="우리팀 인적 네트워크", layout="wide")
st.title("🕸️ 데이터분석랩 인적 네트워크")

st.markdown(
    """
- MBTI 기반 인적 네트워크 시각화  
- 공통 속성(소속, 탄생년도, MBTI, 혈액형 등)으로 간선 생성  
- 노드를 클릭하면 프로필 / 연결 통계 / 비슷한 사람 TOP3 표시  
"""
)

# ---------------- Sidebar ----------------
st.sidebar.header("⚙️ 시각화 설정")
physics = st.sidebar.selectbox("물리엔진", ["barnes_hut", "force_atlas_2based", "repulsion"], index=1)
base_node_size = st.sidebar.slider("기본 노드 크기", 5, 60, 16)
degree_scale = st.sidebar.slider("차수 기반 크기 스케일", 0, 40, 5)
show_labels = st.sidebar.checkbox("이름 라벨 표시", value=True)

st.sidebar.markdown("---")
st.sidebar.header("🔎 MBTI 필터")
ei_filter = st.sidebar.selectbox("E/I 필터", ["(전체)", "E만", "I만"], index=0)
tf_filter = st.sidebar.selectbox("T/F 필터", ["(전체)", "T만", "F만"], index=0)
mbti_exact_placeholder = st.sidebar.empty()  # 나중에 실제 옵션 채움

# 🧵 엣지 타입 토글
st.sidebar.markdown("---")
st.sidebar.header("🧵 엣지 타입 토글")

# 전체 토글 (켜면 모든 엣지 타입을 강제로 사용)
show_edge_all      = st.sidebar.checkbox("전체", value=False)

# 기본으로 켜둘 것: 소속, 탄생년도, MBTI, 혈액형
show_edge_dept     = st.sidebar.checkbox("소속", value=True)
show_edge_role     = st.sidebar.checkbox("직위", value=False)
show_edge_birth    = st.sidebar.checkbox("탄생년도", value=True)
show_edge_cohort   = st.sidebar.checkbox("동기", value=False)
show_edge_kakao    = st.sidebar.checkbox("카카오 분사", value=False)
show_edge_sex      = st.sidebar.checkbox("성별", value=False)
show_edge_joinyear = st.sidebar.checkbox("입사년도", value=False)
show_edge_mbti     = st.sidebar.checkbox("MBTI", value=True)
show_edge_blood    = st.sidebar.checkbox("혈액형", value=True)

st.sidebar.markdown("---")
# 검색 박스를 이 위치에 넣기 위해 placeholder 사용
search_box_placeholder = st.sidebar.empty()

st.sidebar.markdown("---")
st.sidebar.header("📄 데이터 업로드")
uploaded_csv = st.sidebar.file_uploader("팀 CSV 업로드", type=["csv"])
uploaded_imgs = st.sidebar.file_uploader(
    "노드 사진 업로드(선택, 여러 개)", type=["png", "jpg", "jpeg"], accept_multiple_files=True
)

# ---------------- Default data ----------------
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
이창욱,carl.lee,데이터테크셀,셀원,개발,1993,2021.11.30,INTP,,2021 공채 동기,,남자,힐링,액티비티,경기도,미혼,carl.png
김범준,breadly.abc,데이터테크셀,셀원,개발,1994,2024.11.18,ISFJ,O,2024 경력직 동기,,남자,,액티비티,서울,기혼,breadly.png
김희원,wonnie.kim,데이터테크셀,셀원,개발,1997,2021.6.23,ENFP,,2021 인턴 동기,,여자,액티비티,힐링,서울,미혼,wonnie.png
박종범,jaybe.park,이상탐지셀,셀장,개발,1990,2019,ESTP,A,,,남자,액티비티,액티비티,서울,기혼,jaybe.png
주철민,iron.min,이상탐지셀,셀원,개발,1988,2018.9.18,INFJ,B,,,남자,힐링,힐링,경기도,미혼,iron.png
김우영,walt.kim,이상탐지셀,셀원,개발,1990,2020.11.24,,,,,남자,액티비티,힐링,경기도,미혼,walt.png
이종우,justin.dev,이상탐지셀,셀원,개발,1995,2021.11.17,INTJ,B,2021 공채 동기,,남자,힐링,힐링,경기도,미혼,justin.png
김혜정,molly.ouo,이상탐지셀,셀원,개발,1999,2023.1.16,ENFJ,B,,,여자,,힐링,서울,미혼,molly.png
"""

if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
else:
    df = pd.read_csv(io.StringIO(default_csv))

# 컬럼 이름 공백 제거/정규화
df.columns = [c.strip() for c in df.columns]

# Image -> image 통일
if "Image" in df.columns and "image" not in df.columns:
    df["image"] = df["Image"]

# 값 공백 제거
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# ---------------- 이미지 파일 처리 ----------------
IMG_DIR = "node_images"
os.makedirs(IMG_DIR, exist_ok=True)
if uploaded_imgs:
    for f in uploaded_imgs:
        with open(os.path.join(IMG_DIR, f.name), "wb") as out:
            out.write(f.read())

# 이미지 매칭 개선 + 진단
def _variants(name: str):
    if not name:
        return []
    base, ext = os.path.splitext(str(name).strip())
    yield f"{base}{ext}"
    yield f"{base.strip().lower()}{ext.lower()}"
    for e in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
        yield f"{base}{e}"
        yield f"{base.strip().lower()}{e}"

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

    # 절대 URL/data URI면 그대로 사용
    if img_col.startswith(("http://", "https://", "data:")):
        return img_col

    candidates = []
    # CSV 파일명 기반 후보
    for v in _variants(img_col):
        if v:
            candidates.append(os.path.join(IMG_DIR, v))

    # ldap 기반 자동 후보
    if ldap_val:
        for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
            candidates.append(os.path.join(IMG_DIR, ldap_val + ext))
            candidates.append(os.path.join(IMG_DIR, ldap_val.lower() + ext))

    for path in candidates:
        if os.path.exists(path):
            return file_to_data_url(path)

    display_name = str(row.get("이름", "")) or ldap_val or "(unknown)"
    want = img_col or f"{ldap_val}.png/.jpg"
    MISSING_IMAGES.add(f"{display_name} -> {want}")
    # 안전 폴백 이미지
    return "https://via.placeholder.com/120?text=No+Image"

# ---------------- 유틸: 연도 정규화 ----------------
YEAR_RE = re.compile(r"(19|20)\d{2}")

def extract_year(v):
    if v is None:
        return None
    s = str(v)
    m = YEAR_RE.search(s)
    if m:
        try:
            return int(m.group())
        except Exception:
            return None
    # '94' 같은 2자리 처리
    m2 = re.search(r"(?<!\d)(\d{2})(?!\d)", s)
    if m2:
        yy = int(m2.group(1))
        return 1900 + yy if yy >= 50 else 2000 + yy
    return None

# 정규화된 연도 컬럼 추가 (필터 등에 활용)
df["탄생년도_Y"] = df.get("탄생년도").apply(extract_year) if "탄생년도" in df.columns else None
df["입사년도_Y"] = df.get("입사년도").apply(extract_year) if "입사년도" in df.columns else None

# ---------------- MBTI 필터 적용 ----------------

def mbti_list(series):
    vals = sorted([m for m in series.dropna().astype(str).unique() if m and m.lower() != "nan"])
    return ["(전체)"] + vals

mbti_exact = mbti_exact_placeholder.selectbox(
    "정확히(선택)",
    options=mbti_list(df.get("MBTI", pd.Series([]))),
    index=0,
    key="mbti_exact",
)


def keep_by_ei(m):
    if ei_filter == "(전체)" or not m:
        return True
    first = str(m)[:1]
    return (ei_filter == "E만" and first == "E") or (ei_filter == "I만" and first == "I")


def keep_by_tf(m):
    if tf_filter == "(전체)" or not m:
        return True
    third = str(m)[2:3] if len(str(m)) >= 3 else ""
    return (tf_filter == "T만" and third == "T") or (tf_filter == "F만" and third == "F")


def keep_by_exact(m):
    return mbti_exact == "(전체)" or (str(m) == mbti_exact)


mask = df.apply(
    lambda r: keep_by_exact(r.get("MBTI"))
    and keep_by_ei(r.get("MBTI"))
    and keep_by_tf(r.get("MBTI")),
    axis=1,
)

# 가공된 뷰
df_vis = df[mask].copy()
if df_vis.empty:
    st.warning("⚠️ 필터 결과가 없습니다. 필터를 완화해 주세요.")
    df_vis = df.copy()

# ---------------- node_id 생성 ----------------

def node_id_from_row(r):
    val = str(r.get("ldap", "") or "").strip()
    return val if val else str(r["이름"])  # ldap 없으면 이름 사용


df["node_id"] = df.apply(node_id_from_row, axis=1)
df_vis["node_id"] = df_vis.apply(node_id_from_row, axis=1)

# ---------------- Sidebar: 검색 박스 ----------------
focus_node = ""
with search_box_placeholder.container():
    st.subheader("🔍 노드 검색")
    query = st.text_input("이름 또는 ldap", key="search_query")
    if query:
        cond = (
            df_vis["이름"].astype(str).str.contains(query, case=False, na=False)
            | df_vis["ldap"].astype(str).str.contains(query, case=False, na=False)
        )
        matches = df_vis[cond]
        if not matches.empty:
            options = [f"{row['이름']} ({row['ldap']})" for _, row in matches.iterrows()]
            choice = st.selectbox("검색 결과", options, key="search_result")
            if "(" in choice and choice.endswith(")"):
                chosen_ldap = choice.split("(")[-1][:-1]
                row = df[df["ldap"] == chosen_ldap].iloc[0]
                focus_node = row["node_id"]
        else:
            st.info("검색 결과가 없습니다.")

# ---------------- 그래프 생성 공통 유틸 ----------------
rank_size = {"실장": 20, "셀장": 16, "셀원": 12}


def is_filled(v):
    if v is None:
        return False
    s = str(v).strip()
    if s == "":
        return False
    if s.lower() in ("nan", "none", "null"):
        return False
    return True


def valid_equal(a, b):
    if not is_filled(a) or not is_filled(b):
        return False
    return str(a).strip() == str(b).strip()

# MBTI 색상 (테두리)
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
    m = str(m or "").strip()
    return MBTI_COLORS.get(m, "#9ca3af")

def is_kakao_division(v):
    """'카카오' 문자열이 들어가면 카카오 분사로 간주"""
    if v is None:
        return False
    return "카카오" in str(v)

# ---------------- 비슷한 사람 TOP3 계산 (엣지 조건과 동일하게) ----------------
similar_map = {}
rows_full = df.to_dict("records")

# 초기화
for r in rows_full:
    similar_map[r.get("node_id")] = []

for i in range(len(rows_full)):
    for j in range(i + 1, len(rows_full)):
        r1, r2 = rows_full[i], rows_full[j]
        nid1, nid2 = r1["node_id"], r2["node_id"]

        reasons = []

        # 소속
        if (show_edge_all or show_edge_dept) and valid_equal(r1.get("소속"), r2.get("소속")):
            reasons.append("소속")

        # 직위
        if (show_edge_all or show_edge_role) and valid_equal(r1.get("직위"), r2.get("직위")):
            reasons.append("직위")

        # 탄생년도
        if (show_edge_all or show_edge_birth) and valid_equal(
            extract_year(r1.get("탄생년도")),
            extract_year(r2.get("탄생년도")),
        ):
            reasons.append("탄생년도")

        # 동기
        if (show_edge_all or show_edge_cohort) and valid_equal(r1.get("동기 여부"), r2.get("동기 여부")):
            reasons.append("동기")

        # 카카오 분사
        if (show_edge_all or show_edge_kakao):
            k1 = is_kakao_division(r1.get("카카오분사"))
            k2 = is_kakao_division(r2.get("카카오분사"))
            if k1 and k2:
                reasons.append("카카오 분사")

        # 성별
        if (show_edge_all or show_edge_sex) and valid_equal(r1.get("성별"), r2.get("성별")):
            reasons.append("성별")

        # 입사년도
        if (show_edge_all or show_edge_joinyear) and valid_equal(
            extract_year(r1.get("입사년도")),
            extract_year(r2.get("입사년도")),
        ):
            reasons.append("입사년도")

        # MBTI
        if (show_edge_all or show_edge_mbti) and valid_equal(r1.get("MBTI"), r2.get("MBTI")):
            reasons.append("MBTI")

        # 혈액형
        if (show_edge_all or show_edge_blood) and valid_equal(r1.get("혈액형"), r2.get("혈액형")):
            reasons.append("혈액형")

        score = len(reasons)
        if score == 0:
            continue

        reason_text = ", ".join(reasons)
        entry1 = {
            "name": r2.get("이름", ""),
            "ldap": r2.get("ldap", ""),
            "score": score,
            "reasons": reason_text,
        }
        entry2 = {
            "name": r1.get("이름", ""),
            "ldap": r1.get("ldap", ""),
            "score": score,
            "reasons": reason_text,
        }

        similar_map[nid1].append(entry1)
        similar_map[nid2].append(entry2)

# 각 노드별 TOP3만 남기기
for nid, lst in similar_map.items():
    lst.sort(key=lambda x: x["score"], reverse=True)
    similar_map[nid] = lst[:3]

# ---------------- 그래프 생성 함수 ----------------

def make_graph(df_people: pd.DataFrame):
    G = nx.Graph()
    for _, r in df_people.iterrows():
        nid = r["node_id"]
        name = str(r["이름"]) if "이름" in r else nid
        dept = str(r.get("소속", ""))
        img = resolve_image(r)
        title = "<br>".join(
            [
                f"이름: {name}",
                f"ldap: {str(r.get('ldap',''))}",
                f"소속: {dept}",
                f"직위: {str(r.get('직위',''))}",
                f"직군: {str(r.get('직군',''))}",
                f"탄생년도: {str(extract_year(r.get('탄생년도')) or '')}",
                f"입사년도: {str(extract_year(r.get('입사년도')) or '')}",
                f"MBTI: {str(r.get('MBTI',''))}",
                f"혈액형: {str(r.get('혈액형',''))}",
                f"동기 여부: {str(r.get('동기 여부',''))}",
            ]
        )
        border_color = mbti_color(r.get("MBTI"))
        color_dict = {
            "border": border_color,
            "background": "#ffffff",
            "highlight": {"border": border_color, "background": "#ffffff"},
            "hover": {"border": border_color, "background": "#f9fafb"},
        }
        node_kwargs = dict(title=title, group=dept, color=color_dict)
        if show_labels:
            node_kwargs["label"] = name
        if img:
            node_kwargs.update(shape="circularImage", image=img)
        G.add_node(nid, **node_kwargs)

    rows = df_people.to_dict("records")
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            r1, r2 = rows[i], rows[j]
            reasons = []  # (edge_type, label)

            # 소속
            if (show_edge_all or show_edge_dept) and valid_equal(r1.get("소속"), r2.get("소속")):
                reasons.append(("소속", "같은 소속"))

            # 직위
            if (show_edge_all or show_edge_role) and valid_equal(r1.get("직위"), r2.get("직위")):
                reasons.append(("직위", "같은 직위"))

            # 탄생년도
            if (show_edge_all or show_edge_birth) and valid_equal(
                extract_year(r1.get("탄생년도")),
                extract_year(r2.get("탄생년도")),
            ):
                reasons.append(("탄생년도", "같은 탄생년도"))

            # 동기
            if (show_edge_all or show_edge_cohort) and valid_equal(r1.get("동기 여부"), r2.get("동기 여부")):
                reasons.append(("동기", "같은 동기"))

            # 카카오 분사 여부
            if (show_edge_all or show_edge_kakao):
                k1 = is_kakao_division(r1.get("카카오분사"))
                k2 = is_kakao_division(r2.get("카카오분사"))
                if k1 and k2:
                    reasons.append(("카카오", "카카오 분사"))

            # 성별
            if (show_edge_all or show_edge_sex) and valid_equal(r1.get("성별"), r2.get("성별")):
                reasons.append(("성별", "같은 성별"))

            # 입사년도
            if (show_edge_all or show_edge_joinyear) and valid_equal(
                extract_year(r1.get("입사년도")),
                extract_year(r2.get("입사년도")),
            ):
                reasons.append(("입사년도", "같은 입사년도"))

            # MBTI
            if (show_edge_all or show_edge_mbti) and valid_equal(r1.get("MBTI"), r2.get("MBTI")):
                reasons.append(("MBTI", "같은 MBTI"))

            # 혈액형
            if (show_edge_all or show_edge_blood) and valid_equal(r1.get("혈액형"), r2.get("혈액형")):
                reasons.append(("혈액형", "같은 혈액형"))

            if len(reasons) == 0:
                continue

            weight = len(reasons)
            edge_type = reasons[0][0]  # 우선순위는 추가 순서대로
            labels = [lab for _, lab in reasons]
            title = " / ".join(labels) + f" (조건 {weight}개 일치)"

            G.add_edge(r1["node_id"], r2["node_id"], weight=weight, title=title, edge_type=edge_type)
    return G


G = make_graph(df_vis)

# ---------------- 네트워크 통계 ----------------
deg = dict(G.degree())
# 소속/MBTI/동기 맵
dept_map = df.set_index("node_id")["소속"].to_dict()
mbti_map = df.set_index("node_id")["MBTI"].to_dict()
cohort_map = df.set_index("node_id")["동기 여부"].to_dict()

stats = {}
for nid in G.nodes():
    dept = dept_map.get(nid, ""); mbti = mbti_map.get(nid, ""); cohort = cohort_map.get(nid, "")
    same_dept = sum(1 for v in dept_map.values() if v == dept) - 1 if dept else 0
    same_mbti = sum(1 for v in mbti_map.values() if v == mbti) - 1 if mbti else 0
    same_cohort = sum(1 for v in cohort_map.values() if v == cohort) - 1 if cohort else 0
    stats[nid] = {"degree": deg.get(nid, 0), "same_dept": max(same_dept, 0), "same_mbti": max(same_mbti, 0), "same_cohort": max(same_cohort, 0)}


def sized(nid):
    row = df.loc[df["node_id"] == nid]
    rank = row["직위"].iloc[0] if not row.empty else ""
    base_rank = {"실장": 20, "셀장": 16, "셀원": 12}.get(str(rank), 12)
    return base_node_size + base_rank + degree_scale * deg.get(nid, 0)

# ---------------- PyVis 네트워크 ----------------
net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black")
if physics == "barnes_hut":
    net.barnes_hut()
elif physics == "force_atlas_2based":
    net.force_atlas_2based()
else:
    net.repulsion()

# 레이아웃: 소속 + 동기 그룹별 클러스터
depths = sorted(df_vis["소속"].dropna().unique())
depth_x = {d: i * 400 for i, d in enumerate(depths)}
cohorts = df_vis["동기 여부"].dropna().astype(str).str.strip()
cohort_vals = sorted([c for c in cohorts.unique() if c])
cohort_y = {c: idx * 250 for idx, c in enumerate(cohort_vals)}
cohort_y["(none)"] = len(cohort_vals) * 250

for n, data in G.nodes(data=True):
    row = df[df["node_id"] == n].iloc[0]
    dept = str(row.get("소속", ""))
    cval = str(row.get("동기 여부", "") or "").strip()
    x = depth_x.get(dept, 0)
    y = cohort_y.get(cval if cval else "(none)", 0)
    net.add_node(n, size=sized(n), x=x, y=y, physics=True, **data)

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

for u, v, data_e in G.edges(data=True):
    edge_type = data_e.get("edge_type", "기타")
    color = EDGE_COLORS.get(edge_type, "#9ca3af")
    w = data_e.get("weight", 1)
    thickness = 1 + (w * 1.3)
    length = max(80, 280 - 40 * w)

    net.add_edge(
        u, v,
        value=thickness,
        title=data_e.get("title", ""),
        color=color,
        length=length
    )

# ---------------- 클릭 패널 & 검색 포커스 JS ----------------
meta = {}
for _, r in df.iterrows():
    nid = r["node_id"]
    meta[nid] = {
        "이름": str(r.get("이름", "")),
        "ldap": str(r.get("ldap", "")),
        "소속": str(r.get("소속", "")),
        "직위": str(r.get("직위", "")),
        "직군": str(r.get("직군", "")),
        "입사년도": str(extract_year(r.get("입사년도")) or ""),
        "MBTI": str(r.get("MBTI", "")),
        "혈액형": str(r.get("혈액형", "")),
        "동기 여부": str(r.get("동기 여부", "")),
        "연결 수": stats.get(nid, {}).get("degree", 0),
        "같은 소속 수": stats.get(nid, {}).get("same_dept", 0),
        "같은 MBTI 수": stats.get(nid, {}).get("same_mbti", 0),
        "같은 동기 수": stats.get(nid, {}).get("same_cohort", 0),
        "similar": similar_map.get(nid, []),
    }

html_file = "network.html"
net.save_graph(html_file)
with open(html_file, "r", encoding="utf-8") as f:
    html_src = f.read()

focus_node_json = json.dumps(focus_node, ensure_ascii=False)

panel_js = f"""
<script>
window.nodeMeta = {json.dumps(meta, ensure_ascii=False)};
(function() {{
  const panelId = 'profilePanel';
  let panel = document.getElementById(panelId);
  if (!panel) {{
    panel = document.createElement('div');
    panel.id = panelId;
    panel.style.position='fixed'; panel.style.top='20px'; panel.style.right='20px';
    panel.style.width='260px'; panel.style.maxHeight='65vh'; panel.style.overflow='auto';
    panel.style.border='1px solid #e5e7eb'; panel.style.borderRadius='12px';
    panel.style.padding='10px'; panel.style.background='rgba(255,255,255,0.9)';
    panel.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)'; panel.style.fontSize='13px';
    panel.style.lineHeight='1.35';
    panel.innerHTML = '<b>노드를 클릭하면 상세 정보가 여기에 표시됩니다.</b><br><small>빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>';
    document.body.appendChild(panel);
  }}
  if (typeof network !== 'undefined') {{
    var nodes = network.body.data.nodes; var edges = network.body.data.edges;
    var allNodes = nodes.get({{returnType:'Object'}}); var allEdges = edges.get({{returnType:'Object'}});
    function focusOnNode(nid) {{
      var connectedNodes = network.getConnectedNodes(nid); connectedNodes.push(nid);
      var updatesNodes = []; for (var id in allNodes) {{
        var visible = connectedNodes.indexOf(id) !== -1 || connectedNodes.indexOf(parseInt(id)) !== -1;
        updatesNodes.push({{id: id, hidden: !visible}});
      }} nodes.update(updatesNodes);
      var connectedEdges = network.getConnectedEdges(nid); var updatesEdges = []; for (var eid in allEdges) {{
        var visibleE = connectedEdges.indexOf(eid) !== -1 || connectedEdges.indexOf(parseInt(eid)) !== -1;
        updatesEdges.push({{id: eid, hidden: !visibleE}});
      }} edges.update(updatesEdges);
      try {{ network.focus(nid, {{scale: 1.5, animation: true}}); }} catch(e) {{}}
    }}
    function resetView() {{
      var updatesNodes = []; for (var id in allNodes) {{ updatesNodes.push({{id: id, hidden: false}}); }} nodes.update(updatesNodes);
      var updatesEdges = []; for (var eid in allEdges) {{ updatesEdges.push({{id: eid, hidden: false}}); }} edges.update(updatesEdges);
      network.fit({{}});
    }}
    var initialFocusNode = {focus_node_json}; if (initialFocusNode) {{ setTimeout(function() {{ try {{ network.selectNodes([initialFocusNode]); focusOnNode(initialFocusNode); }} catch(e) {{}} }}, 600); }}
    network.on('click', function(params) {{
      if (params.nodes && params.nodes.length > 0) {{
        var nid = params.nodes[0]; var m = (window.nodeMeta || {{}})[nid] || {{}};
        var sims = m['similar'] || []; var simsHtml = '';
        if (sims.length > 0) {{
          simsHtml += '<hr><div><b>가장 비슷한 사람 TOP3</b><ol style="padding-left:18px; margin:4px 0;">';
          for (var i = 0; i < sims.length; i++) {{
            var s = sims[i]; var label = (s.name || '') + (s.ldap ? ' (' + s.ldap + ')' : '');
            var reasonTxt = s.reasons ? ' - ' + s.reasons + ' 일치' : '';
            simsHtml += '<li>' + label + ' (조건 ' + (s.score || 0) + '개 일치' + reasonTxt + ')</li>';
          }} simsHtml += '</ol></div>';
        }}
        panel.innerHTML =
          '<h3 style="margin:0 0 6px 0;">' + (m['이름']||nid) + '</h3>' +
          '<div><b>ldap</b>: ' + (m['ldap']||'') + '</div>' +
          '<div><b>소속</b>: ' + (m['소속']||'') + '</div>' +
          '<div><b>직위</b>: ' + (m['직위']||'') + '</div>' +
          '<div><b>직군</b>: ' + (m['직군']||'') + '</div>' +
          '<div><b>입사년도</b>: ' + (m['입사년도']||'') + '</div>' +
          '<div><b>MBTI</b>: ' + (m['MBTI']||'') + '</div>' +
          '<div><b>혈액형</b>: ' + (m['혈액형']||'') + '</div>' +
          '<div><b>동기 여부</b>: ' + (m['동기 여부']||'') + '</div>' +
          '<hr>' +
          '<div><b>연결 수</b>: ' + (m['연결 수']||0) + '</div>' +
          '<div><b>같은 소속 인원</b>: ' + (m['같은 소속 수']||0) + '</div>' +
          '<div><b>같은 MBTI 인원</b>: ' + (m['같은 MBTI 수']||0) + '</div>' +
          '<div><b>같은 동기 인원</b>: ' + (m['같은 동기 수']||0) + '</div>' +
          simsHtml +
          '<hr><small>이 노드와 연결된 관계만 표시됩니다. 빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>';
        focusOnNode(nid);
      }} else {{ panel.innerHTML = '<b>노드를 클릭하면 상세 정보가 여기에 표시됩니다.</b><br><small>빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>'; resetView(); }}
    }});
  }}
}})();
</script>
"""

html_src = html_src.replace("</body>", panel_js + "\n</body>")

# 🔍 엣지 색상 설명 (네트워크 위쪽)
legend_html = """
<div style="margin-top:8px; font-size:13px;">
  <b>엣지 색상 의미</b><br>
  <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:4px;">
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#22c55e;"></span> 소속
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#16a34a;"></span> 직위
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#0ea5e9;"></span> 탄생년도
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#3b82f6;"></span> 동기
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#f59e0b;"></span> 카카오 분사
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#ec4899;"></span> 성별
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#a855f7;"></span> 입사년도
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#ef4444;"></span> MBTI
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#f97316;"></span> 혈액형
    </span>
  </div>
  <div style="margin-top:2px; color:#6b7280;">(선이 두꺼울수록 조건이 더 많이 겹친다는 뜻)</div>
</div>
"""
st.markdown(legend_html, unsafe_allow_html=True)

html(html_src, height=820, scrolling=True)

# ❗미해결 이미지 목록 표시
if MISSING_IMAGES:
    st.sidebar.markdown("### ❗미해결 이미지")
    for msg in sorted(MISSING_IMAGES):
        st.sidebar.write(msg)


def generate_team_intro(df: pd.DataFrame) -> str:
    """
    df를 요약해서 팀 소개글 초안을 만들어주는 함수 (OpenAI 사용)
    """
    wanted_cols = [
        "이름", "소속", "직위", "직군",
        "입사년도", "MBTI", "혈액형",
        "워크샵성향(2025)", "거주지",
    ]
    cols = [c for c in wanted_cols if c in df.columns]
    people = df[cols].to_dict(orient="records")

    if len(people) > 100:
        people = people[:100]

    messages = [
        {
            "role": "system",
            "content": (
                "너는 한국 IT 회사의 데이터분석팀 소개글을 써주는 작가야. "
                "사내 위키/노션에 올릴 문서라고 생각하고, 너무 딱딱하지 않은 존댓말 톤으로 작성해줘."
            ),
        },
        {
            "role": "user",
            "content": f"""
다음은 우리 팀원들의 정보야. (각 항목은 JSON 한 줄로 되어 있음)

- 팀 전체적인 특징 (규모, 소속 구성, 역할/직군, MBTI 분포 느낌 등)
- 일할 때 분위기/컬러
- 워크샵/회식 스타일 한두 가지 제안
- 새로 합류한 사람에게 해주면 좋을 한 줄 조언

위 4가지를 중심으로, 4~7단락 정도의 한국어 소개글을 작성해줘.
이름은 일일이 다 나열하지 말고, 전체적인 경향 위주로 써줘.

[팀 데이터]
{people}
""",
        },
    ]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",   # 또는 gpt-4.1-mini
        messages=messages,
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip()





# --------- 막대 그래프 헬퍼 ---------
def plot_bar_with_labels(data, title, xlabel="", ylabel=""):
    fig, ax = plt.subplots()
    bars = ax.bar(data.index.astype(str), data.values)

    for bar in bars:
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2,
            yval,
            f"{yval:.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

# ---------------- 📊 MBTI / 입사년도 + I/E, T/F ----------------
with st.expander("📊 MBTI / 입사년도 분포 + I/E · T/F 비율"):
    col1, col2 = st.columns(2)

    # 전체 MBTI 분포
    mbti_series = df["MBTI"].dropna().astype(str).str.strip()
    mbti_series = mbti_series[mbti_series != ""]
    if not mbti_series.empty:
        mbti_counts = mbti_series.value_counts().sort_index()
        col1.markdown("**MBTI 분포**")
        fig = plot_bar_with_labels(mbti_counts, "MBTI 분포", ylabel="Count")
        col1.pyplot(fig)
    else:
        col1.info("MBTI 데이터가 없습니다.")

    # 입사년도 분포
    if "입사년도" in df.columns:
        years = df["입사년도"].apply(extract_year).dropna().astype(int)
        if not years.empty:
            year_counts = years.value_counts().sort_index()
            col2.markdown("**입사년도 분포 (정규화)**")
            fig2 = plot_bar_with_labels(year_counts, "입사년도 분포", ylabel="Count")
            col2.pyplot(fig2)
        else:
            col2.info("입사년도 데이터가 없습니다.")
    else:
        col2.info("입사년도 컬럼이 없습니다.")

    st.markdown("---")
    st.markdown("### 🌍 전체 MBTI I/E, T/F 비율 (파이차트)")

    # 전체 I/E, T/F 비율
    if "MBTI" in df.columns:
        overall_mbti = df["MBTI"].dropna().astype(str).str.strip()
        overall_mbti = overall_mbti[overall_mbti != ""]
        overall_mbti = overall_mbti[overall_mbti.str.len() >= 3]
        overall_mbti = overall_mbti[~overall_mbti.str.contains(r"\?", regex=True)]

        if not overall_mbti.empty:
            overall_IE = overall_mbti.str[0]   # I / E
            overall_TF = overall_mbti.str[2]   # T / F

            p1, p2 = st.columns(2)

            # 전체 I/E 파이차트
            ie_counts_overall = overall_IE.value_counts()
            count_I = int(ie_counts_overall.get("I", 0))
            count_E = int(ie_counts_overall.get("E", 0))

            if count_I + count_E > 0:
                fig_ie, ax_ie = plt.subplots()
                ax_ie.pie(
                    [count_I, count_E],
                    labels=[f"I ({count_I})", f"E ({count_E})"],
                    autopct="%1.1f%%",
                    startangle=90,
                )
                ax_ie.axis("equal")
                p1.markdown("**전체 I / E 비율**")
                p1.pyplot(fig_ie)
            else:
                p1.info("I/E 비율을 계산할 수 있는 데이터가 없습니다.")

            # 전체 T/F 파이차트
            tf_counts_overall = overall_TF.value_counts()
            count_T = int(tf_counts_overall.get("T", 0))
            count_F = int(tf_counts_overall.get("F", 0))

            if count_T + count_F > 0:
                fig_tf, ax_tf = plt.subplots()
                ax_tf.pie(
                    [count_T, count_F],
                    labels=[f"T ({count_T})", f"F ({count_F})"],
                    autopct="%1.1f%%",
                    startangle=90,
                )
                ax_tf.axis("equal")
                p2.markdown("**전체 T / F 비율**")
                p2.pyplot(fig_tf)
            else:
                p2.info("T/F 비율을 계산할 수 있는 데이터가 없습니다.")
        else:
            st.info("전체 I/E, T/F 비율을 계산할 수 있는 유효한 MBTI 데이터가 없습니다.")
    else:
        st.info("`MBTI` 컬럼이 없어 전체 비율을 계산할 수 없습니다.")

    st.markdown("---")
    st.markdown("### 🧬 소속별 MBTI I/E, T/F 비율 (데이터분석랩 제외)")

    if "MBTI" in df.columns and "소속" in df.columns:
        df_mbti = df[["소속", "MBTI"]].dropna().copy()
        df_mbti["MBTI"] = df_mbti["MBTI"].astype(str).str.strip()
        df_mbti = df_mbti[df_mbti["MBTI"].str.len() >= 3]
        df_mbti = df_mbti[~df_mbti["MBTI"].str.contains(r"\?", regex=True)]
        df_mbti = df_mbti[df_mbti["소속"] != "데이터분석랩"]

        if not df_mbti.empty:
            df_mbti["IE"] = df_mbti["MBTI"].str[0]
            df_mbti["TF"] = df_mbti["MBTI"].str[2]

            col3, col4 = st.columns(2)

            # 소속별 I/E 비율
            ie_counts = df_mbti.groupby(["소속", "IE"]).size().unstack(fill_value=0)
            for c in ["I", "E"]:
                if c not in ie_counts.columns:
                    ie_counts[c] = 0

            denom_ie = (ie_counts["I"] + ie_counts["E"]).replace(0, pd.NA)
            ie_ratio_I = (ie_counts["I"] / denom_ie).fillna(0)
            ie_ratio_E = (ie_counts["E"] / denom_ie).fillna(0)

            ie_ratio_df = pd.DataFrame(
                {
                    "I 비율": ie_ratio_I,
                    "E 비율": ie_ratio_E,
                }
            )
            ie_ratio_percent = ie_ratio_df * 100
            ie_ratio_flat = ie_ratio_percent.stack()
            ie_ratio_flat.index = [
                f"{dept} - {kind}" for dept, kind in ie_ratio_flat.index
            ]

            col3.markdown("**소속별 I / E 비율 (%)**")
            fig3 = plot_bar_with_labels(ie_ratio_flat, "소속별 I/E 비율 (%)", ylabel="%")
            col3.pyplot(fig3)

            # 소속별 T/F 비율
            tf_counts = df_mbti.groupby(["소속", "TF"]).size().unstack(fill_value=0)
            for c in ["T", "F"]:
                if c not in tf_counts.columns:
                    tf_counts[c] = 0

            denom_tf = (tf_counts["T"] + tf_counts["F"]).replace(0, pd.NA)
            tf_ratio_T = (tf_counts["T"] / denom_tf).fillna(0)
            tf_ratio_F = (tf_counts["F"] / denom_tf).fillna(0)

            tf_ratio_df = pd.DataFrame(
                {
                    "T 비율": tf_ratio_T,
                    "F 비율": tf_ratio_F,
                }
            )
            tf_ratio_percent = tf_ratio_df * 100
            tf_ratio_flat = tf_ratio_percent.stack()
            tf_ratio_flat.index = [
                f"{dept} - {kind}" for dept, kind in tf_ratio_flat.index
            ]

            col4.markdown("**소속별 T / F 비율 (%)**")
            fig4 = plot_bar_with_labels(tf_ratio_flat, "소속별 T/F 비율 (%)", ylabel="%")
            col4.pyplot(fig4)

        else:
            st.info("소속별 MBTI 비율을 계산할 수 있는 유효한 MBTI 데이터가 없습니다. (또는 모두 데이터분석랩이라 제외됨)")
    else:
        st.info("`소속` 또는 `MBTI` 컬럼이 없어 소속별 비율을 계산할 수 없습니다.")


# ---------------- 📝 AI 팀 소개글 ----------------
with st.expander("📝 AI가 써주는 팀 소개글 초안"):
    st.markdown(
        """
CSV에 있는 정보를 바탕으로  
**데이터분석랩 / 각 셀의 분위기, MBTI 경향, 워크샵/회식 스타일** 등을
한 번에 요약한 소개글 초안을 만들어 줍니다.
"""
    )
    if st.button("팀 소개글 생성하기"):
        with st.spinner("팀 소개글 생성 중입니다..."):
            try:
                intro_text = generate_team_intro(df)  # 🔹 필터 전 원본 df 기준
                st.markdown(intro_text)
            except Exception as e:
                st.error(f"생성 중 오류가 발생했어요: {e}")




# ---------------- 포스터 뷰 (소속 팀별 인쇄용) ----------------
with st.expander("🖼 팀 구성도 포스터 뷰 (소속별 인쇄용 레이아웃)"):
    st.markdown("브라우저에서 `Print` → `PDF로 저장` 하면 소속별 포스터처럼 쓸 수 있어요.")
    if "소속" in df.columns:
        for dept, sub in df.groupby("소속"):
            st.markdown(f"### 🏷 {dept}")
            cols = st.columns(4)
            for idx, (_, r) in enumerate(sub.iterrows()):
                col = cols[idx % 4]
                img = resolve_image(r)
                if img:
                    col.image(img, width=120)
                jy = extract_year(r.get("입사년도"))
                col.markdown(
                    f"**{r.get('이름','')}**  \n"
                    f"{r.get('직위','')} / {r.get('직군','')}  \n"
                    f"{(jy or '')} 입사 · {r.get('MBTI','')}"
                )
            st.markdown("---")
    else:
        st.info("소속 컬럼이 없어 포스터 뷰를 만들 수 없습니다.")

# ---------------- 데이터 미리보기 ----------------
with st.expander("데이터 미리보기(필터 적용)"):
    st.dataframe(df_vis)
