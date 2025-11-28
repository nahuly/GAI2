# app.py
import base64
import os, io, json
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html
import networkx as nx
from pyvis.network import Network

st.set_page_config(page_title="우리팀 인적 네트워크", layout="wide")
st.title("🕸️ 우리팀 인적 네트워크 (ldap 지원)")

st.markdown("""
**필수 컬럼:** `이름, ldap, 소속, 직위, 직군, 탄생년도`  
**선택 컬럼:** `입사년도, MBTI, 혈액형, 동기 여부, image`  
- **노드 ID = ldap**(없으면 이름), **라벨 = 이름**  
- 색상=소속, 크기=직위(실장>셀장>셀원)  
- 간선=공통 속성: 소속(+2), 직군(+1), 입사년도(+3), 동기 여부(+4), MBTI(E/I 동일 +0.5)  
- **노드 클릭** → 우측 패널에 상세 프로필 표시  
- **MBTI 필터** (정확히, E/I, T/F)
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
mbti_exact_placeholder = st.sidebar.empty()  # 아래에서 실제 옵션으로 교체

st.sidebar.markdown("---")
st.sidebar.header("📄 데이터 업로드")
uploaded_csv = st.sidebar.file_uploader("팀 CSV 업로드", type=["csv"])
uploaded_imgs = st.sidebar.file_uploader(
    "노드 사진 업로드(선택, 여러 개)", type=["png","jpg","jpeg"], accept_multiple_files=True
)

# ---------------- Default data (네가 준 최신 표 반영) ----------------
default_csv = """이름,ldap,소속,직위,직군,탄생년도,입사년도,MBTI,혈액형,동기 여부
김수형,Cantabile,데이터분석랩,실장,개발,1970,,,, 
김선영,Party.92,BI셀,셀장,기술,1984,,ESFJ,A,
송대섭,Steven.song,BI셀,셀원,개발,1989,,,, 
이나연,Zoe.lee93,BI셀,셀원,개발,1993,2022,INFJ,A,
유선정,saylor.u,BI셀,셀원,기술,1994,2023,INFP,A,
조승민,noah.94,BI셀,셀원,기술,1994,2024,ESFJ,,2024 입사 동기
김용환,Feno,BI셀,셀원,개발,1994,2024,INFP,,2024 입사 동기
강동진,sonny.kang,BI셀,셀원,기술,1995,2021,ESFP,,2021 인턴 동기
조윤영,Zoey.cho,BI셀,셀원,개발,1996,2021,INTJ,,2021 인턴 동기
조은희,Alysia.,데이터테크셀,셀장,개발,1980,,INTP,, 
정동주,Dj.jeong,데이터테크셀,셀원,개발,1988,,ISFP,, 
윤태식,Levi.y,데이터테크셀,셀원,개발,1992,,,, 
이창욱,carl.lee,데이터테크셀,셀원,개발,1993,2021,INTP,,2021 공채 동기
김범준,Broadly,데이터테크셀,셀원,개발,1994,2024,,,2024 입사 동기
김희원,Wonnie,데이터테크셀,셀원,개발,1997,2021,ENFP,,2021 인턴 동기
박종범,jaybe.park,이상탐지셀,셀장,개발,1990,,,, 
주철민,Iron.min,이상탐지셀,셀원,개발,1988,,INFJ,, 
김우영,Walt.kim,이상탐지셀,셀원,개발,1990,,,, 
이종우,Justin.dev,이상탐지셀,셀원,개발,1995,2021,INTJ,,2021 공채 동기
김혜정,Molly.ouo,이상탐지셀,셀원,개발,1999,2023,ENFJ,,
"""

if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
else:
    df = pd.read_csv(io.StringIO(default_csv))

# 컬럼 이름 양쪽 공백 제거
df.columns = [c.strip() for c in df.columns]

# Image(대문자) → image(소문자)로 통일
if "Image" in df.columns and "image" not in df.columns:
    df["image"] = df["Image"]

# ---------------- Images ----------------
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
        mime = "image/jpeg"  # jpg, jpeg 등
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{data}"


def resolve_image(row):
    # 1) CSV의 image 컬럼 우선 사용
    img_col = str(row.get("image", "")).strip()
    candidates = []

    if img_col:
        # URL이면 그대로 사용
        if img_col.startswith("http://") or img_col.startswith("https://") or img_col.startswith("data:"):
            return img_col
        # 파일명이면 node_images 안에서 찾기 후보에 추가
        candidates.append(os.path.join(IMG_DIR, img_col))

    # 2) image 비어 있으면 ldap 기반 자동 매칭 후보 추가
    ldap_val = str(row.get("ldap", "")).strip()
    if ldap_val:
        for ext in (".png", ".jpg", ".jpeg"):
            candidates.append(os.path.join(IMG_DIR, ldap_val + ext))

    # 3) 존재하는 첫 번째 파일을 data URL로 변환
    for path in candidates:
        if os.path.exists(path):
            return file_to_data_url(path)

    # 4) 못 찾으면 빈 문자열
    return ""


# ---------------- Filters ----------------
def mbti_list(series):
    vals = sorted([m for m in series.dropna().astype(str).unique() if m and m.lower() != "nan"])
    return ["(전체)"] + vals

mbti_exact = mbti_exact_placeholder.selectbox("정확히(선택)", options=mbti_list(df["MBTI"]), index=0, key="mbti_exact")

def keep_by_ei(m):
    if ei_filter == "(전체)" or not m: return True
    first = str(m)[:1]
    return (ei_filter == "E만" and first == "E") or (ei_filter == "I만" and first == "I")

def keep_by_tf(m):
    if tf_filter == "(전체)" or not m: return True
    third = str(m)[2:3] if len(str(m)) >= 3 else ""
    return (tf_filter == "T만" and third == "T") or (tf_filter == "F만" and third == "F")

def keep_by_exact(m):
    return mbti_exact == "(전체)" or (str(m) == mbti_exact)

mask = df.apply(lambda r: keep_by_exact(r.get("MBTI")) and keep_by_ei(r.get("MBTI")) and keep_by_tf(r.get("MBTI")), axis=1)
df_vis = df[mask].copy()
if df_vis.empty:
    st.warning("⚠️ 필터 결과가 없습니다. 필터를 완화해 주세요.")
    df_vis = df.copy()

# ---------------- Graph building ----------------
rank_size = {"실장": 20, "셀장": 16, "셀원": 12}

# node_id: ldap 우선, 없으면 이름
def node_id_from_row(r):
    val = str(r.get("ldap","")).strip()
    return val if val else str(r["이름"])

df_vis["node_id"] = df_vis.apply(node_id_from_row, axis=1)
df["node_id"] = df.apply(node_id_from_row, axis=1)  # 전체 데이터 기준 메타용

st.write(df[["이름", "ldap", "image"]])


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

        node_kwargs = dict(title=title, group=dept)
        if show_labels:
            node_kwargs["label"] = name
        if img:
            node_kwargs.update(shape="circularImage", image=img)

        G.add_node(nid, **node_kwargs)

    # --------- 엣지 생성 규칙 ----------
    rows = df_people.to_dict("records")

    def is_filled(v):
        """빈 값 / NaN / None / 공백은 전부 '값 없음'으로 본다."""
        if v is None:
            return False
        s = str(v).strip()
        if s == "":
            return False
        if s.lower() in ("nan", "none", "null"):
            return False
        return True

    def valid_equal(a, b):
        """둘 다 '실제 값'이 있고, 같을 때만 True."""
        if not is_filled(a) or not is_filled(b):
            return False
        return str(a).strip() == str(b).strip()


    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            r1, r2 = rows[i], rows[j]
            reasons = []
            weight = 0

            # 1) 같은 소속
            if valid_equal(r1.get("소속"), r2.get("소속")):
                weight += 1
                reasons.append("같은 소속")

            # 2) 셀장끼리 (둘 다 '셀장'이고 값 존재)
            pos1 = str(r1.get("직위", "")).strip()
            pos2 = str(r2.get("직위", "")).strip()
            if pos1 == "셀장" and pos2 == "셀장":
                weight += 1
                reasons.append("셀장끼리")

            # 3) 같은 입사년도
            if valid_equal(r1.get("입사년도"), r2.get("입사년도")):
                weight += 1
                reasons.append("같은 입사년도")

            # 4) 같은 MBTI
            if valid_equal(r1.get("MBTI"), r2.get("MBTI")):
                weight += 1
                reasons.append("같은 MBTI")

            # 5) 같은 혈액형
            if valid_equal(r1.get("혈액형"), r2.get("혈액형")):
                weight += 1
                reasons.append("같은 혈액형")

            # 6) 같은 동기 여부 (비었으면 비교 제외)
            if valid_equal(r1.get("동기 여부"), r2.get("동기 여부")):
                weight += 1
                reasons.append("같은 동기")

            # ---- 조건 충족이 하나도 없다면 edge 생성 X ----
            if weight == 0:
                continue

            # edge 대표 타입 결정 (우선순위)
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

deg = dict(G.degree())
def sized(nid):
    # 원본 df에서 node_id로 직위 조회
    row = df.loc[df["node_id"] == nid]
    rank = row["직위"].iloc[0] if not row.empty else ""
    return base_node_size + rank_size.get(str(rank), 12) + degree_scale * deg.get(nid, 0)

net = Network(height="800px", width="100%", bgcolor="#ffffff", font_color="black")
if physics == "barnes_hut":
    net.barnes_hut()
elif physics == "force_atlas_2based":
    net.force_atlas_2based()
else:
    net.repulsion()

for n, data in G.nodes(data=True):
    net.add_node(n, size=sized(n), **data)
# 🎨 조건별 색상 매핑
EDGE_COLORS = {
    "소속": "#22c55e",      # green  (같은 소속)
    "동기": "#3b82f6",      # blue   (같은 동기)
    "입사년도": "#a855f7",  # purple
    "MBTI": "#ef4444",      # red
    "혈액형": "#f97316",    # orange
    "셀장": "#000000",      # black
}

for u, v, data in G.edges(data=True):
    edge_type = data.get("edge_type")
    color = EDGE_COLORS.get(edge_type, "#999999")  # 기본 회색
    net.add_edge(
        u,
        v,
        value=data.get("weight", 1),
        title=data.get("title", ""),
        color=color,
    )


# ---------------- Click detail panel (HTML injection) ----------------
# 클릭용 메타: node_id 키로 저장
meta = {}
for _, r in df.iterrows():  # 전체 데이터(필터 전)
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
    }

html_file = "network.html"
net.save_graph(html_file)
with open(html_file, "r", encoding="utf-8") as f:
    html_src = f.read()

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
    panel.style.width='240px';
    panel.style.maxHeight='60vh';
    panel.style.overflow='auto';
    panel.style.border='1px solid #e5e7eb';
    panel.style.borderRadius='12px';
    panel.style.padding='10px';
    panel.style.background='rgba(255,255,255,0.85)';  // 반투명
    panel.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)';
    panel.style.fontSize='13px';
    lineHeight='1.3';
    panel.innerHTML = '<b>노드를 클릭하면 상세 정보가 여기에 표시됩니다.</b><br><small>빈 공간을 클릭하면 전체 네트워크가 다시 보입니다.</small>';
    document.body.appendChild(panel);
  }}
  if (typeof network !== 'undefined') {{
    // vis-network의 DataSet
    var nodes = network.body.data.nodes;
    var edges = network.body.data.edges;
    var allNodes = nodes.get({{returnType:'Object'}});
    var allEdges = edges.get({{returnType:'Object'}});

    function focusOnNode(nid) {{
      // nid와 연결된 노드/엣지만 보이도록 hidden 플래그 조정
      var connectedNodes = network.getConnectedNodes(nid);
      connectedNodes.push(nid); // 자기 자신 추가

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
    }}

    function resetView() {{
      // 모든 노드/엣지를 다시 보이게
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
    }}

    network.on('click', function(params) {{
      if (params.nodes && params.nodes.length > 0) {{
        // 노드 클릭
        var nid = params.nodes[0];
        var m = (window.nodeMeta || {{}})[nid] || {{}};
        panel.innerHTML =
          '<h3 style="margin:0 0 8px 0;">' + (m['이름']||nid) + '</h3>' +
          '<div><b>ldap</b>: ' + (m['ldap']||'') + '</div>' +
          '<div><b>소속</b>: ' + (m['소속']||'') + '</div>' +
          '<div><b>직위</b>: ' + (m['직위']||'') + '</div>' +
          '<div><b>직군</b>: ' + (m['직군']||'') + '</div>' +
          '<div><b>입사년도</b>: ' + (m['입사년도']||'') + '</div>' +
          '<div><b>MBTI</b>: ' + (m['MBTI']||'') + '</div>' +
          '<div><b>혈액형</b>: ' + (m['혈액형']||'') + '</div>' +
          '<div><b>동기 여부</b>: ' + (m['동기 여부']||'') + '</div>' +
          '<hr><small>이 노드와 연결된 관계만 표시됩니다. 빈 공간을 클릭하면 전체가 다시 보입니다.</small>';
        focusOnNode(nid);
      }} else {{
        // 배경 클릭 → 전체 리셋
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

with st.expander("데이터 미리보기(필터 적용)"):
    st.dataframe(df_vis)
