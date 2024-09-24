import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from io import StringIO

# Streamlit 앱 설정
st.title('Character Relationship Diagram Generator')

# 파일 업로드
uploaded_file = st.file_uploader("Upload a text file", type="txt")

if uploaded_file is not None:
    # 파일 읽기
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    story_text = stringio.read()

    # 관계도 생성 (예시로 간단한 관계 설정)
    G = nx.Graph()

    # 예시 인물 및 관계 추가
    G.add_edge("Henry Jekyll", "Edward Hyde", relationship="같은 인물")
    G.add_edge("Henry Jekyll", "John Utterson", relationship="친구")
    G.add_edge("Henry Jekyll", "Dr. Hastie Lanyon", relationship="동료")
    G.add_edge("Henry Jekyll", "Emma Carew", relationship="약혼자")
    G.add_edge("Emma Carew", "Danvers Carew", relationship="부녀")
    G.add_edge("Edward Hyde", "Lucy", relationship="폭력적 관계")

    # 그래프 그리기
    pos = nx.spring_layout(G)
    plt.figure(figsize=(8, 6))

    nx.draw(G, pos, with_labels=True, node_color='lightblue',
            font_weight='bold', node_size=3000)

    # 관계 라벨 추가
    edge_labels = nx.get_edge_attributes(G, 'relationship')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # Streamlit에 그래프 표시
    st.pyplot(plt)
