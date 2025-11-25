# network_demo.py
import networkx as nx
import matplotlib.pyplot as plt

# 1) 그래프 만들기: 노드와 간선 정의
nodes = ["A", "B", "C", "D", "E", "F"]
edges = [
    ("A", "B"),
    ("A", "C"),
    ("B", "C"),
    ("C", "D"),
    ("D", "E"),
    ("E", "F"),
    ("B", "E"),
]

G = nx.Graph()
G.add_nodes_from(nodes)
G.add_edges_from(edges)

# 2) 레이아웃(노드 좌표) 계산
pos = nx.spring_layout(G, seed=42)  # seed 고정하면 매번 같은 배치

# 3) 노드 크기를 '연결수(차수)'에 비례하도록
degrees = dict(G.degree())
node_sizes = [200 + degrees[n] * 400 for n in G.nodes()]  # 기본 200, 차수마다 +400

# 4) 그리기
plt.figure(figsize=(6, 6))
nx.draw_networkx_nodes(G, pos, node_size=node_sizes, edgecolors="black")
nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7)
nx.draw_networkx_labels(G, pos, font_size=10)

plt.axis("off")
plt.tight_layout()
plt.savefig("network.png", dpi=200)  # 결과를 이미지로 저장
plt.show()
