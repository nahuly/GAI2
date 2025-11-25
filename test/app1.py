# app.py
import os, io, json, base64
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html
import networkx as nx
from pyvis.network import Network

# ---------------- 기본 설정 ----------------
st.set_page_config(page_title="우리팀 인적 네트워크", layout="wide")
st.title("🕸️ 우리팀 인적 네트워크 (강화 버전)")

st.markdown("""
**필수 컬럼:** `이름, ldap, 소속, 직위, 직군, 탄생년도`  
**선택 컬럼:** `입사년도, MBTI, 혈액형, 동기 여부, Image/image`  

- 노드 ID = **ldap**(없으면 이름), 라벨 = 이름  
- 색상(테두리) = **MBTI 기반**  
- 레이아웃 = **소속 + 동기 그룹별 클러스터링**  
- 간선 = 공통 속성 (소속, 셀장, 입사년도, MBTI, 혈액형, 동기)  
- 엣지 색 = 조건별로 다름 (소속, 동기, 입사년도, MBTI, 혈액형, 셀장)  
- 엣지 길이 = 조건이 많을수록 가까이 (튜브맵 느낌)  
- 노드 클릭 → 연결된 관계만 표시 + 상세 프로필 + 네트워크 통계 + 비슷한 사람 TOP3  
- MBTI 필터 + 노드 검색(Search)  
- 아래에 **팀 구성도 포스터 뷰(그리드)** + **MBTI/입사년도 분포 차트** 제공
""")

# ---------------- Sidebar ----------------
st.sidebar.header("⚙️ 시각화 설정")
physics = st.sidebar.selectbox("물리엔진", ["barnes_hut","force_atlas_2based","repulsion"], index=1)
base_node_size = st.sidebar.slider("기본 노드 크기", 5, 60, 16)
degree_scale = st.sidebar.slider("차수 기반 크기 스케일", 0, 40, 10)
show_labels = st.sidebar.checkbox("이름 라벨 표시", value=True)

st.sidebar.markdown("---")
st.sidebar.header("🔎 MBTI 필터")
ei_filter = st.sidebar.selectbox("E/I 필터", ["(전체)","E만","I만"], index=0)
tf_filter = st.sidebar.selectbox("T/F 필터", ["(전체)","T만","F만"], index=0)
mbti_exact_placeholder = st.sidebar.empty()   # 나중에 실제 옵션 채움

# 🧵 엣지 타입 토글
st.sidebar.markdown("---")
st.sidebar.header("🧵 엣지 타입 토글")
show_edge_dept     = st.sidebar.checkbox("같은 소속", value=True)
show_edge_cohort   = st.sidebar.checkbox("같은 동기", value=True)
show_edge_joinyear = st.sidebar.checkbox("같은 입사년도", value=True)
show_edge_mbti     = st.sidebar.checkbox("같은 MBTI", value=True)
show_edge_blood    = st.sidebar.checkbox("같은 혈액형", value=True)
show_edge_leader   = st.sidebar.checkbox("셀장끼리", value=True)

st.sidebar.markdown("---")
# 검색 박스를 이 위치에 넣기 위해 placeholder 사용
search_box_placeholder = st.sidebar.empty()

st.sidebar.markdown("---")
st.sidebar.header("📄 데이터 업로드")
uploaded_csv = st.sidebar.file_uploader("팀 CSV 업로드", type=["csv"])
uploaded_imgs = st.sidebar.file_uploader(
    "노드 사진 업로드(선택, 여러 개)", type=["png","jpg","jpeg"], accept_multiple_files=True
)

# ---------------- Default data ----------------
default_csv = """이름,ldap,소속,직위,직군,탄생년도,입사년도,MBTI,혈액형,동기 여부,Image
김수형,cantabile.58,데이터분석랩,실장,개발,1970,,,,,cantabile.png
김선영,party.92,BI셀,셀장,기술,1984,,ESFJ,A,,party.png
송대섭,steven.song,BI셀,셀원,개발,1989,,,,,steven.png
이나연,zoe.lee93,BI셀,셀원,개발,1993,2022,INFJ,A,,zoe.png
유선정,saylor.u,BI셀,셀원,기술,1994,2023,INFP,A,,saylor.png
조승민,noah.94,BI셀,셀원,기술,1994,2024,ESFJ,,2024 입사 동기,noah.png
김용환,feno.meno,BI셀,셀원,개발,1994,2024,INFP,,2024 입사 동기,feno.png
강동진,sonny.kang,BI셀,셀원,기술,1995,2021,ESFP,,2021 인턴 동기,sonny.png
조윤영,zoey.cho,BI셀,셀원,개발,1996,2021,INTJ,,2021 인턴 동기,zoey.png
조은희,alysia.c,데이터테크셀,셀장,개발,1980,,INTP,,,alysia.png
정동주,dj.jeong,데이터테크셀,셀원,개발,1988,,ISFP,,,dj.png
윤태식,levi.y,데이터테크셀,셀원,개발,1992,,,,,levi.png
이창욱,carl.lee,데이터테크셀,셀원,개발,1993,2021,INTP,,2021 공채 동기,carl.png
김범준,breadly.abc,데이터테크셀,셀원,개발,1994,2024,,,2024 입사 동기,breadly.png
김희원,wonnie.kim,데이터테크셀,셀원,개발,1997,2021,ENFP,,2021 인턴 동기,wonnie.png
박종범,jaybe.park,이상탐지셀,셀장,개발,1990,,,,,jaybe.png
주철민,iron.min,이상탐지셀,셀원,개발,1988,,INFJ,,,iron.png
김우영,walt.kim,이상탐지셀,셀원,개발,1990,,,,,walt.png
이종우,justin.dev,이상탐지셀,셀원,개발,1995,2021,INTJ,,2021 공채 동기,justin.png
김혜정,molly.ouo,이상탐지셀,셀원,개발,1999,2023,ENFJ,,,molly.png
"""

if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
else:
    df = pd.read_csv(io.StringIO(default_csv))

# 컬럼 이름 정리
df.columns = [c.strip() for c in df.columns]

# Image -> image 통일
if "Image" in df.columns and "image" not in df.columns:
    df["image"] = df["Image"]

# ---------------- 이미지 파일 처리 ----------------
IMG_DIR = "node_images"
os.makedirs(IMG_DIR, exist_ok=True)
if uploaded_imgs:
    for f in uploaded_imgs:
        with open(os.path.join(IMG_DIR, f.name), "wb") as out:
            out.write(f.read())

def file_to_data_url(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".png":
        mime = "image/png"
    else:
        mime = "image/jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{data}"

def resolve_image(row):
    # 1) CSV의 image 컬럼 우선 사용
    img_col = str(row.get("image", "") or "").strip()
    candidates = []

    if img_col:
        if img_col.startswith("http://") or img_col.startswith("https://") or img_col.startswith("data:"):
            return img_col
        candidates.append(os.path.join(IMG_DIR, img_col))

    # 2) 비어 있으면 ldap 기반 자동 매칭
    ldap_val = str(row.get("ldap", "") or "").strip()
    if ldap_val:
        for ext in (".png", ".jpg", ".jpeg"):
            candidates.append(os.path.join(IMG_DIR, ldap_val + ext))

    for path in candidates:
        if os.path.exists(path):
            return file_to_data_url(path)

    return ""

# ---------------- MBTI 필터 적용 ----------------
def mbti_list(series):
    vals = sorted([m for m in series.dropna().astype(str).unique() if m and m.lower() != "nan"])
    return ["(전체)"] + vals

mbti_exact = mbti_exact_placeholder.selectbox(
    "정확히(선택)",
    options=mbti_list(df.get("MBTI", pd.Series([]))),
    index=0,
    key="mbti_exact"
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

mask = df.apply(lambda r: keep_by_exact(r.get("MBTI")) and keep_by_ei(r.get("MBTI")) and keep_by_tf(r.get("MBTI")), axis=1)
df_vis = df[mask].copy()
if df_vis.empty:
    st.warning("⚠️ 필터 결과가 없습니다. 필터를 완화해 주세요.")
    df_vis = df.copy()

# ---------------- node_id 생성 ----------------
def node_id_from_row(r):
    val = str(r.get("ldap", "") or "").strip()
    return val if val else str(r["이름"])

df["node_id"] = df.apply(node_id_from_row, axis=1)
df_vis["node_id"] = df_vis.apply(node_id_from_row, axis=1)

# ---------------- Sidebar: 검색 박스 ----------------
focus_node = ""
with search_box_placeholder.container():
    st.subheader("🔍 노드 검색")
    query = st.text_input("이름 또는 ldap", key="search_query")
    if query:
        cond = (
            df_vis["이름"].astype(str).str.contains(query, case=False, na=False) |
            df_vis["ldap"].astype(str).str.contains(query, case=False, na=False)
        )
        matches = df_vis[cond]
        if not matches.empty:
            options = [f"{row['이름']} ({row['ldap']})" for _, row in matches.iterrows()]
            choice = st.selectbox("검색 결과", options, key="search_result")
            # 괄호 안의 ldap 추출
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

# ---------------- 비슷한 사람 TOP3 계산 ----------------
similar_map = {nid: [] for nid in df["node_id"]}

rows_full = df.to_dict("records")
for i in range(len(rows_full)):
    for j in range(i + 1, len(rows_full)):
        r1, r2 = rows_full[i], rows_full[j]
        nid1, nid2 = r1["node_id"], r2["node_id"]
        reasons = []
        score = 0

        # 같은 소속
        if valid_equal(r1.get("소속"), r2.get("소속")):
            score += 1; reasons.append("소속")
        # 같은 직군
        if valid_equal(r1.get("직군"), r2.get("직군")):
            score += 1; reasons.append("직군")
        # 같은 입사년도
        if valid_equal(r1.get("입사년도"), r2.get("입사년도")):
            score += 1; reasons.append("입사년도")
        # 같은 MBTI
        if valid_equal(r1.get("MBTI"), r2.get("MBTI")):
            score += 1; reasons.append("MBTI")
        # 같은 혈액형
        if valid_equal(r1.get("혈액형"), r2.get("혈액형")):
            score += 1; reasons.append("혈액형")
        # 같은 동기
        if valid_equal(r1.get("동기 여부"), r2.get("동기 여부")):
            score += 1; reasons.append("동기")

        if score == 0:
            continue

        entry1 = {
            "name": r2.get("이름",""),
            "ldap": r2.get("ldap",""),
            "score": int(score),
            "reasons": ", ".join(reasons),
        }
        entry2 = {
            "name": r1.get("이름",""),
            "ldap": r1.get("ldap",""),
            "score": int(score),
            "reasons": ", ".join(reasons),
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

    # 노드 추가
    for _, r in df_people.iterrows():
        nid = r["node_id"]
        name = str(r["이름"])
        dept = str(r["소속"])
        img = resolve_image(r)

        title = "<br>".join([
            f"이름: {name}",
            f"ldap: {str(r.get('ldap',''))}",
            f"소속: {dept}",
            f"직위: {str(r.get('직위',''))}",
            f"직군: {str(r.get('직군',''))}",
            f"입사년도: {str(r.get('입사년도',''))}",
            f"MBTI: {str(r.get('MBTI',''))}",
            f"혈액형: {str(r.get('혈액형',''))}",
            f"동기 여부: {str(r.get('동기 여부',''))}",
        ])

        # MBTI 기반 테두리 색
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

    # --------- 엣지 생성 규칙 (토글 반영) ----------
    rows = df_people.to_dict("records")

    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            r1, r2 = rows[i], rows[j]
            reasons = []
            weight = 0

            # 1) 같은 소속
            if show_edge_dept and valid_equal(r1.get("소속"), r2.get("소속")):
                weight += 1
                reasons.append("같은 소속")

            # 2) 셀장끼리
            pos1 = str(r1.get("직위", "") or "").strip()
            pos2 = str(r2.get("직위", "") or "").strip()
            if show_edge_leader and pos1 == "셀장" and pos2 == "셀장":
                weight += 1
                reasons.append("셀장끼리")

            # 3) 같은 입사년도
            if show_edge_joinyear and valid_equal(r1.get("입사년도"), r2.get("입사년도")):
                weight += 1
                reasons.append("같은 입사년도")

            # 4) 같은 MBTI
            if show_edge_mbti and valid_equal(r1.get("MBTI"), r2.get("MBTI")):
                weight += 1
                reasons.append("같은 MBTI")

            # 5) 같은 혈액형
            if show_edge_blood and valid_equal(r1.get("혈액형"), r2.get("혈액형")):
                weight += 1
                reasons.append("같은 혈액형")

            # 6) 같은 동기
            if show_edge_cohort and valid_equal(r1.get("동기 여부"), r2.get("동기 여부")):
                weight += 1
                reasons.append("같은 동기")

            if weight == 0:
                continue

            # 대표 edge_type (색칠용, 우선순위)
            if "같은 동기" in reasons:
                edge_type = "동기"
            elif "같은 소속" in reasons:
                edge_type = "소속"
            elif "같은 입사년도" in reasons:
                edge_type = "입사년도"
            elif "같은 MBTI" in reasons:
                edge_type = "MBTI"
            elif "같은 혈액형" in reasons:
                edge_type = "혈액형"
            elif "셀장끼리" in reasons:
                edge_type = "셀장"
            else:
                edge_type = "기타"

            title = " / ".join(reasons)
            title = f"{title} (조건 {weight}개 일치)"

            G.add_edge(
                r1["node_id"],
                r2["node_id"],
                weight=weight,
                title=title,
                edge_type=edge_type,
            )

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
    dept = dept_map.get(nid, "")
    mbti = mbti_map.get(nid, "")
    cohort = cohort_map.get(nid, "")
    same_dept = sum(1 for v in dept_map.values() if v == dept) - 1 if dept else 0
    same_mbti = sum(1 for v in mbti_map.values() if v == mbti) - 1 if mbti else 0
    same_cohort = sum(1 for v in cohort_map.values() if v == cohort) - 1 if cohort else 0

    stats[nid] = {
        "degree": deg.get(nid, 0),
        "same_dept": max(same_dept, 0),
        "same_mbti": max(same_mbti, 0),
        "same_cohort": max(same_cohort, 0),
    }

def sized(nid):
    row = df.loc[df["node_id"] == nid]
    rank = row["직위"].iloc[0] if not row.empty else ""
    base_rank = rank_size.get(str(rank), 12)
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
depts = sorted(df_vis["소속"].dropna().unique())
dept_x = {d: i * 400 for i, d in enumerate(depts)}

cohorts = df_vis["동기 여부"].dropna().astype(str).str.strip()
cohort_vals = sorted([c for c in cohorts.unique() if c])
cohort_y = {c: idx * 250 for idx, c in enumerate(cohort_vals)}
cohort_y["(none)"] = len(cohort_vals) * 250  # 동기 없음

for n, data in G.nodes(data=True):
    row = df[df["node_id"] == n].iloc[0]
    dept = str(row.get("소속", ""))
    cval = str(row.get("동기 여부", "") or "").strip()
    x = dept_x.get(dept, 0)
    y = cohort_y.get(cval if cval else "(none)", 0)
    net.add_node(n, size=sized(n), x=x, y=y, physics=True, **data)

# 엣지 색상 + 튜브맵 거리
EDGE_COLORS = {
    "소속": "#22c55e",      # green
    "동기": "#3b82f6",      # blue
    "입사년도": "#a855f7",  # purple
    "MBTI": "#ef4444",      # red
    "혈액형": "#f97316",    # orange
    "셀장": "#000000",      # black
    "기타": "#9ca3af",
}

for u, v, data_e in G.edges(data=True):
    edge_type = data_e.get("edge_type", "기타")
    color = EDGE_COLORS.get(edge_type, "#9ca3af")
    w = data_e.get("weight", 1)
    length = max(80, 280 - 40 * w)  # weight 많을수록 더 가까이
    net.add_edge(
        u,
        v,
        value=w,
        title=data_e.get("title", ""),
        color=color,
        length=length,
    )

# ---------------- 클릭 패널 & 검색 포커스 JS ----------------
# 클릭용 메타: node_id 키
meta = {}
for _, r in df.iterrows():
    nid = r["node_id"]
    meta[nid] = {
        "이름": str(r.get("이름","")),
        "ldap": str(r.get("ldap","")),
        "소속": str(r.get("소속","")),
        "직위": str(r.get("직위","")),
        "직군": str(r.get("직군","")),
        "입사년도": str(r.get("입사년도","")),
        "MBTI": str(r.get("MBTI","")),
        "혈액형": str(r.get("혈액형","")),
        "동기 여부": str(r.get("동기 여부","")),
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
    panel.style.position='fixed';
    panel.style.top='20px';
    panel.style.right='20px';
    panel.style.width='260px';
    panel.style.maxHeight='65vh';
    panel.style.overflow='auto';
    panel.style.border='1px solid #e5e7eb';
    panel.style.borderRadius='12px';
    panel.style.padding='10px';
    panel.style.background='rgba(255,255,255,0.9)';
    panel.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)';
    panel.style.fontSize='13px';
    panel.style.lineHeight='1.35';
    panel.innerHTML = '<b>노드를 클릭하면 상세 정보가 여기에 표시됩니다.</b><br><small>빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>';
    document.body.appendChild(panel);
  }}
  if (typeof network !== 'undefined') {{
    var nodes = network.body.data.nodes;
    var edges = network.body.data.edges;
    var allNodes = nodes.get({{returnType:'Object'}});
    var allEdges = edges.get({{returnType:'Object'}});

    function focusOnNode(nid) {{
      var connectedNodes = network.getConnectedNodes(nid);
      connectedNodes.push(nid);

      var updatesNodes = [];
      for (var id in allNodes) {{
        var visible =
          connectedNodes.indexOf(id) !== -1 ||
          connectedNodes.indexOf(parseInt(id)) !== -1;
        updatesNodes.push({{id: id, hidden: !visible}});
      }}
      nodes.update(updatesNodes);

      var connectedEdges = network.getConnectedEdges(nid);
      var updatesEdges = [];
      for (var eid in allEdges) {{
        var visibleE =
          connectedEdges.indexOf(eid) !== -1 ||
          connectedEdges.indexOf(parseInt(eid)) !== -1;
        updatesEdges.push({{id: eid, hidden: !visibleE}});
      }}
      edges.update(updatesEdges);

      try {{
        network.focus(nid, {{scale: 1.5, animation: true}});
      }} catch(e) {{}}
    }}

    function resetView() {{
      var updatesNodes = [];
      for (var id in allNodes) {{
        updatesNodes.push({{id: id, hidden: false}});
      }}
      nodes.update(updatesNodes);

      var updatesEdges = [];
      for (var eid in allEdges) {{
        updatesEdges.push({{id: eid, hidden: false}});
      }}
      edges.update(updatesEdges);
      network.fit({{}});
    }}

    // 검색으로 선택된 노드가 있으면 자동 포커스
    var initialFocusNode = {focus_node_json};
    if (initialFocusNode) {{
      setTimeout(function() {{
        try {{
          network.selectNodes([initialFocusNode]);
          focusOnNode(initialFocusNode);
        }} catch(e) {{}}
      }}, 600);
    }}

    network.on('click', function(params) {{
      if (params.nodes && params.nodes.length > 0) {{
        var nid = params.nodes[0];
        var m = (window.nodeMeta || {{}})[nid] || {{}};

        var sims = m['similar'] || [];
        var simsHtml = '';
        if (sims.length > 0) {{
          simsHtml += '<hr><div><b>가장 비슷한 사람 TOP3</b><ol style="padding-left:18px; margin:4px 0;">';
          for (var i = 0; i < sims.length; i++) {{
            var s = sims[i];
            var label = (s.name || '') + (s.ldap ? ' (' + s.ldap + ')' : '');
            var reasonTxt = s.reasons ? ' - ' + s.reasons + ' 일치' : '';
            simsHtml += '<li>' + label + ' (조건 ' + (s.score || 0) + '개 일치' + reasonTxt + ')</li>';
          }}
          simsHtml += '</ol></div>';
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
          '<hr><small>이 노드와 연결된 관계만 표시됩니다. 빈 공간을 클릭하면 전체가 다시 보입니다.</small>';
        focusOnNode(nid);
      }} else {{
        panel.innerHTML =
          '<b>노드를 클릭하면 상세 정보가 여기에 표시됩니다.</b><br><small>빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>';
        resetView();
      }}
    }});
  }}
}})();
</script>
"""

html_src = html_src.replace("</body>", panel_js + "\n</body>")
html(html_src, height=820, scrolling=True)

# 🔍 엣지 색상 설명
legend_html = """
<div style="margin-top:8px; font-size:13px;">
  <b>엣지 색상 의미</b><br>
  <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:4px;">
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#22c55e;"></span> 같은 소속
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#3b82f6;"></span> 같은 동기
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#a855f7;"></span> 같은 입사년도
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#ef4444;"></span> 같은 MBTI
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#f97316;"></span> 같은 혈액형
    </span>
    <span style="display:inline-flex; align-items:center; gap:4px;">
      <span style="display:inline-block; width:14px; height:4px; background:#000000;"></span> 셀장끼리
    </span>
  </div>
  <div style="margin-top:2px; color:#6b7280;">(선이 두꺼울수록 조건이 더 많이 겹친다는 뜻)</div>
</div>
"""
st.markdown(legend_html, unsafe_allow_html=True)

# ---------------- 📊 MBTI / 입사년도 분포 차트 ----------------
with st.expander("📊 MBTI / 입사년도 분포 차트"):
    col1, col2 = st.columns(2)

    # MBTI 분포
    mbti_series = df["MBTI"].dropna().astype(str).str.strip()
    mbti_series = mbti_series[mbti_series != ""]
    if not mbti_series.empty:
        mbti_counts = mbti_series.value_counts().sort_index()
        col1.markdown("**MBTI 분포**")
        col1.bar_chart(mbti_counts)
    else:
        col1.info("MBTI 데이터가 없습니다.")

    # 입사년도 분포
    if "입사년도" in df.columns:
        join_year = pd.to_numeric(df["입사년도"], errors="coerce")
        join_year = join_year.dropna().astype(int)
        if not join_year.empty:
            year_counts = join_year.value_counts().sort_index()
            col2.markdown("**입사년도 분포**")
            col2.bar_chart(year_counts)
        else:
            col2.info("입사년도 데이터가 없습니다.")
    else:
        col2.info("입사년도 컬럼이 없습니다.")

# ---------------- 포스터 뷰 (인쇄용) ----------------
with st.expander("🖼 팀 구성도 포스터 뷰 (인쇄용 레이아웃)"):
    st.markdown("브라우저에서 `Print` → `PDF로 저장` 하면 포스터처럼 쓸 수 있어요.")
    cols = st.columns(4)
    for idx, (_, r) in enumerate(df.iterrows()):
        col = cols[idx % 4]
        img = resolve_image(r)
        if img:
            col.image(img, width=120)
        col.markdown(
            f"**{r.get('이름','')}**  \n"
            f"{r.get('소속','')} / {r.get('직위','')}  \n"
            f"{str(r.get('입사년도','') or '').split('.')[0]} 입사 · {r.get('MBTI','')}"
        )

# ---------------- 데이터 미리보기 ----------------
with st.expander("데이터 미리보기(필터 적용)"):
    st.dataframe(df_vis)
