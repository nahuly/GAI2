import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

st.title("📱 카톡 대화 관계 분석기 (정렬 · 인기별 표시 적용)")

uploaded_file = st.file_uploader("talk1.csv 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # 필수 컬럼 체크
    required_cols = {"Date", "User", "Message"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"필수 컬럼이 없습니다: {', '.join(missing)}")
        st.stop()

    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)
    df.dropna(subset=["User"], inplace=True)
    df["User"] = df["User"].astype(str).str.strip()

    # 참여자 및 라벨 매핑
    users = df["User"].unique().tolist()
    user_map = {u: f"User{idx+1}" for idx, u in enumerate(users)}

    # 유저별 메시지 수 (내림차순)
    msg_count = df["User"].value_counts().sort_values(ascending=False)

    st.subheader("👥 대화 참여자")
    st.write(", ".join(users))
    st.caption("한글 → 영문 라벨 매핑 (네트워크에서 사용)")
    map_df = pd.DataFrame({
        "Original(한글)": msg_count.index,
        "Label(영문)": [user_map[u] for u in msg_count.index],
        "Messages": msg_count.values
    })
    st.dataframe(map_df, use_container_width=True)

    # 유저별 메시지 수 (내림차순 그래프)
    st.subheader("📊 유저별 메시지 수")
    st.bar_chart(msg_count)

    # 평균 응답 시간(초) = 상대 메시지 이후 내가 보낸 첫 메시지
    df["PrevDate"] = df["Date"].shift(1)
    df["PrevUser"] = df["User"].shift(1)
    df["ResponseTime"] = (df["Date"] - df["PrevDate"]).dt.total_seconds()
    response_df = df[df["User"] != df["PrevUser"]].copy()

    avg_response = (
        response_df.groupby("User")["ResponseTime"]
        .mean().round(2)
        .sort_values(ascending=False)  # 내림차순
        .rename("AverageReplySeconds").to_frame()
    )
    st.subheader("⏱ 평균 응답 시간 (초)")
    st.dataframe(avg_response, use_container_width=True)

    # 친밀도(방향성) raw 계산
    directed_edges = []
    for i in range(1, len(df)):
        p, c = df.iloc[i-1]["User"], df.iloc[i]["User"]
        if p != c:
            directed_edges.append((p, c))

    from collections import Counter
    edge_counter = Counter(directed_edges)

    dir_scores = []
    raw_scores = []
    for (u1, u2), inter_cnt in edge_counter.items():
        rts = response_df[(response_df["PrevUser"] == u1) & (response_df["User"] == u2)]["ResponseTime"]
        if len(rts) > 0 and rts.notna().any():
            resp_minutes = rts.mean() / 60.0
            resp_score = 1.0 / (resp_minutes + 1.0)  # 빠를수록 ↑
        else:
            resp_score = 0.0
        raw = inter_cnt + resp_score
        raw_scores.append(raw)
        dir_scores.append({"From": u1, "To": u2, "RawScore": raw})

    max_raw = max(raw_scores) if raw_scores else 1.0
    for row in dir_scores:
        row["Score100"] = round((row["RawScore"] / max_raw) * 100.0, 2)

    rel_df = pd.DataFrame(dir_scores)

    # (1) 요청: 친밀도 지수는 From, To, Score100만 + 내림차순
    st.subheader("💞 친밀도 지수 (100점 만점, 방향성)")
    if rel_df.empty:
        st.warning("계산 가능한 친밀도 지수가 없습니다.")
    else:
        rel_simple = rel_df[["From", "To", "Score100"]].sort_values("Score100", ascending=False)
        st.dataframe(rel_simple, use_container_width=True)

    # 시간대 패턴 (사용자별 100%) — 행(사용자) 정렬은 메시지 수 내림차순 기준
    def get_time_period(h):
        if 5 <= h < 12: return "아침"
        if 12 <= h < 18: return "점심/오후"
        if 18 <= h < 22: return "저녁"
        return "밤"
    df["Period"] = df["Date"].dt.hour.apply(get_time_period)
    count_tbl = df.groupby(["User", "Period"]).size().unstack(fill_value=0)
    pct_tbl = (count_tbl.div(count_tbl.sum(axis=1), axis=0) * 100).round(2)
    desired_cols = ["아침","점심/오후","저녁","밤"]
    pct_tbl = pct_tbl.reindex(columns=[c for c in desired_cols if c in pct_tbl.columns])
    # 사용자 인덱스를 메시지 수 기준 내림차순으로 재정렬
    pct_tbl = pct_tbl.reindex(index=msg_count.index)

    st.subheader("🕒 대화 시간대 패턴 (사용자별 100%)")
    st.dataframe(pct_tbl, use_container_width=True)
    st.bar_chart(pct_tbl)

    # --- 네트워크 위에 참여자 표 한 번 더 (요청 1) ---
    st.subheader("👥 대화 참여자 (네트워크 섹션용)")
    st.dataframe(map_df, use_container_width=True)

    # (2)(3) 네트워크 그래프: 범례 제거, 인기(= in-weight 합) 큰 노드는 별표(*)로 표시
    st.subheader("🔗 대화 관계 네트워크 (영문 라벨 + 방향, 인기별 크기/모양)")

    if not rel_df.empty:
        G = nx.DiGraph()
        for _, r in rel_df.iterrows():
            u_from = user_map[r["From"]]
            u_to = user_map[r["To"]]
            G.add_edge(u_from, u_to, weight=r["Score100"], label=r["Score100"])

        pos = nx.spring_layout(G, seed=42)
        plt.figure(figsize=(8, 8))

        # 인기도: 들어오는 가중치(Score100)의 합
        in_weights = {n: 0.0 for n in G.nodes()}
        for u, v, d in G.edges(data=True):
            in_weights[v] += d.get("weight", 0.0)

        # 최대 인기도 노드(들)
        if len(in_weights) > 0:
            max_in = max(in_weights.values())
            top_nodes = [n for n, val in in_weights.items() if val == max_in]
        else:
            max_in = 0.0
            top_nodes = []

        # 노드 크기 스케일링
        vals = list(in_weights.values()) if in_weights else [0]
        vmin, vmax = (min(vals), max(vals)) if vals else (0, 1)
        def scale(x, min_size=1200, max_size=4200):
            if vmax == vmin:
                return (min_size + max_size) / 2
            return min_size + (x - vmin) * (max_size - min_size) / (vmax - vmin)
        node_sizes = {n: scale(in_weights[n]) for n in G.nodes()}

        # 일반 노드(원형)
        normal_nodes = [n for n in G.nodes() if n not in top_nodes]
        if normal_nodes:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=normal_nodes,
                node_size=[node_sizes[n] for n in normal_nodes],
                node_color="lightblue",
                node_shape="o"  # 동그라미
            )

        # 인기 최상위 노드(별표) — 여러 명일 수 있음
        if top_nodes:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=top_nodes,
                node_size=[max(node_sizes[n], 1600) for n in top_nodes],  # 최소 사이즈 보정
                node_color="lightblue",
                node_shape="*"  # 별표
            )

        # 라벨
        nx.draw_networkx_labels(G, pos, font_size=12)

        # 엣지 (두께=가중치 비례)
        weights = [G[u][v]["weight"] for u, v in G.edges()]
        nx.draw_networkx_edges(
            G, pos,
            arrows=True, arrowstyle="-|>", arrowsize=20,
            width=[max(1.0, w/20.0) for w in weights]
        )

        # 엣지 라벨 (점수)
        edge_labels = {(u, v): f'{G[u][v]["label"]}' for u, v in G.edges()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

        # 범례는 제거 요청 → 추가하지 않음
        plt.tight_layout()
        st.pyplot(plt)
    else:
        st.info("표시할 네트워크가 없습니다.")

    # 이모티콘 비율 (내림차순)
    st.subheader("😀 이모티콘 사용 비율 (%)")
    df["IsEmoji"] = df["Message"].astype(str).str.contains("이모티콘|😂|🤣|❤️|👍|ㅠㅠ|ㅎㅎ|ㅋ", regex=True)
    emoji_ratio = (df.groupby("User")["IsEmoji"].mean() * 100).round(2).sort_values(ascending=False)
    st.bar_chart(emoji_ratio)
