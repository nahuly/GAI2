import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

st.title("📱 카톡 대화 관계 분석기 (개선版)")

# ---------------------------
# 파일 업로드
# ---------------------------
uploaded_file = st.file_uploader("talk1.csv 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # 필수 컬럼 체크
    required_cols = {"Date", "User", "Message"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"필수 컬럼이 없습니다: {', '.join(missing)}")
        st.stop()

    # 날짜 파싱 및 정리
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)
    # nan 제거 (특히 User 컬럼)
    df.dropna(subset=["User"], inplace=True)
    df["User"] = df["User"].astype(str).str.strip()

    # ---------------------------
    # (2) 대화 참여자 표시 + 영문 라벨 매핑
    # ---------------------------
    users = df["User"].unique().tolist()
    user_map = {u: f"User{idx+1}" for idx, u in enumerate(users)}  # 한글명 -> ASCII 라벨
    st.subheader("👥 대화 참여자")
    st.write(", ".join(users))

    st.caption("아래 매핑을 네트워크 그래프 등에 사용합니다 (한글 → 영문 라벨).")
    map_df = pd.DataFrame({"Original(한글)": users, "Label(영문)": [user_map[u] for u in users]})
    st.dataframe(map_df, use_container_width=True)

    # ---------------------------
    # (메시지 수)
    # ---------------------------
    st.subheader("📊 유저별 메시지 수")
    msg_count = df["User"].value_counts()
    st.bar_chart(msg_count)

    # ---------------------------
    # (3) 평균 응답 시간(초)
    #    => '바로 직전 메시지의 작성자'가 나와 다를 때만 계산 = 실제 '답장' 시간
    # ---------------------------
    df["PrevDate"] = df["Date"].shift(1)
    df["PrevUser"] = df["User"].shift(1)
    df["ResponseTime"] = (df["Date"] - df["PrevDate"]).dt.total_seconds()

    # 사용자 변경(=상대에게 답장)인 경우만 남김
    response_df = df[df["User"] != df["PrevUser"]].copy()

    # 평균 응답시간: "내가 남에게 답한" 시간의 평균
    avg_response = (
        response_df.groupby("User")["ResponseTime"]
        .mean()
        .round(2)
        .sort_values()
        .rename("AverageReplySeconds")
        .to_frame()
    )

    st.subheader("⏱ 평균 응답 시간 (초)")
    st.dataframe(avg_response)

    # ---------------------------
    # (4) 친밀도 지수: 100점 만점으로 정규화
    #  - 방향성 있는 간선 기준 (u1 -> u2)
    #  - raw_score = (u1->u2 전환 횟수) + (응답속도 점수; 빠를수록 ↑)
    #  - 응답속도 점수 = 1 / (평균 응답(분) + 1)
    #  - 그 뒤 전체 최대 raw_score로 0~100 정규화
    # ---------------------------
    # 방향 전환(edge) 목록 (직전 사용자 -> 현재 사용자)
    directed_edges = []
    for i in range(1, len(df)):
        prev_user = df.iloc[i - 1]["User"]
        curr_user = df.iloc[i]["User"]
        if prev_user != curr_user:
            directed_edges.append((prev_user, curr_user))

    # 전환 횟수 집계
    from collections import Counter, defaultdict
    edge_counter = Counter(directed_edges)

    # 방향별 응답시간: (u1->u2) 전환에 대해 "u2가 u1에게 답하는데 걸린 시간"
    # response_df는 이미 사용자 변경만 남아있으므로, (PrevUser=u1 & User=u2) 필터 사용
    dir_scores = []
    raw_scores = []
    for (u1, u2), inter_count in edge_counter.items():
        rt_series = response_df[(response_df["PrevUser"] == u1) & (response_df["User"] == u2)]["ResponseTime"]
        if len(rt_series) > 0 and rt_series.notna().any():
            resp_minutes = rt_series.mean() / 60.0
            resp_score = 1.0 / (resp_minutes + 1.0)  # 빠를수록 커짐 (0~1 사이)
        else:
            resp_score = 0.0
        raw = inter_count + resp_score
        raw_scores.append(raw)
        dir_scores.append({"From": u1, "To": u2, "InteractionCount": inter_count, "RespScore": round(resp_score, 4), "RawScore": raw})

    max_raw = max(raw_scores) if raw_scores else 1.0
    for row in dir_scores:
        row["Score100"] = round((row["RawScore"] / max_raw) * 100.0, 2)

    rel_df = pd.DataFrame(dir_scores)
    if rel_df.empty:
        st.warning("대화 전환(서로 주고받기)이 거의 없어 친밀도 지수를 계산할 수 없습니다.")
    else:
        # 한글 컬럼도 보여주고, 영문 라벨도 병기
        rel_df_show = rel_df.copy()
        rel_df_show.insert(0, "From(Label)", rel_df_show["From"].map(user_map))
        rel_df_show.insert(1, "To(Label)", rel_df_show["To"].map(user_map))
        st.subheader("💞 친밀도 지수 (100점 만점, 방향성)")
        st.caption("RawScore를 전 방향 중 최대값으로 정규화했습니다. (전환 횟수↑, 응답 빠름↑)")
        st.dataframe(rel_df_show[[
            "From", "To", "From(Label)", "To(Label)", "InteractionCount", "RespScore", "RawScore", "Score100"
        ]], use_container_width=True)

    # ---------------------------
    # (5) 대화 시간대 패턴: 사용자별 합 100%가 되도록 비율화
    # ---------------------------
    def get_time_period(hour: int) -> str:
        if 5 <= hour < 12:
            return "아침"
        elif 12 <= hour < 18:
            return "점심/오후"
        elif 18 <= hour < 22:
            return "저녁"
        else:
            return "밤"

    df["Period"] = df["Date"].dt.hour.apply(get_time_period)
    count_tbl = df.groupby(["User", "Period"]).size().unstack(fill_value=0)

    # 행(사용자) 기준 합 100% 정규화
    pct_tbl = (count_tbl.div(count_tbl.sum(axis=1), axis=0) * 100).round(2)
    # Period 컬럼 순서를 보기 좋게 재정렬
    desired_cols = ["아침", "점심/오후", "저녁", "밤"]
    pct_tbl = pct_tbl.reindex(columns=[c for c in desired_cols if c in pct_tbl.columns])

    st.subheader("🕒 대화 시간대 패턴 (사용자별 100%)")
    st.dataframe(pct_tbl, use_container_width=True)
    st.bar_chart(pct_tbl)

    # ---------------------------
    # (6) 네트워크 그래프: 영문 라벨 + 방향 화살표 + 점수(100점)
    # ---------------------------
    st.subheader("🔗 대화 관계 네트워크 (영문 라벨 + 방향)")

    if not rel_df.empty:
        # DiGraph 구성: 가중치는 100점 점수 사용
        G = nx.DiGraph()
        for _, r in rel_df.iterrows():
            u_from = user_map[r["From"]]
            u_to = user_map[r["To"]]
            G.add_edge(u_from, u_to, weight=r["Score100"], label=r["Score100"])

        pos = nx.spring_layout(G, seed=42, k=None)
        plt.figure(figsize=(7, 7))

        # 노드/엣지 그리기
        nx.draw_networkx_nodes(G, pos, node_size=3000, node_color="lightblue")
        nx.draw_networkx_labels(G, pos, font_size=12)

        # 엣지 두께를 점수에 비례
        weights = [G[u][v]["weight"] for u, v in G.edges()]
        # 화살표 있는 엣지 그리기
        nx.draw_networkx_edges(
            G, pos,
            arrows=True, arrowstyle="-|>", arrowsize=20,
            width=[max(1.0, w/20.0) for w in weights]  # 0~100점 -> 대략 1~5 굵기
        )

        # 엣지 라벨(점수)
        edge_labels = {(u, v): f'{G[u][v]["label"]}' for u, v in G.edges()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

        st.pyplot(plt)
    else:
        st.info("표시할 네트워크가 없습니다.")

    # ---------------------------
    # (6-보너스) 이모티콘 비율 (그대로 유지)
    # ---------------------------
    st.subheader("😀 이모티콘 사용 비율 (%)")
    # 간단 패턴 (원하는 경우 정교한 이모지 탐지로 확장 가능)
    df["IsEmoji"] = df["Message"].astype(str).str.contains("이모티콘|😂|🤣|❤️|👍|ㅠㅠ|ㅎㅎ|ㅋ", regex=True)
    emoji_ratio = (df.groupby("User")["IsEmoji"].mean() * 100).round(2)
    st.bar_chart(emoji_ratio)
