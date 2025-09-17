import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

st.title("📱 카톡 대화 관계 분석기")

# ---------------------------
# 파일 업로드
# ---------------------------
uploaded_file = st.file_uploader("talk1.csv 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df["Date"] = pd.to_datetime(df["Date"])

    # nan 제거 (특히 User 컬럼에 빈 값 방지)
    df.dropna(subset=["User"], inplace=True)

    st.subheader("원본 데이터 미리보기")
    st.dataframe(df.head())

    # ---------------------------
    # 메시지 수 분석
    # ---------------------------
    st.subheader("📊 유저별 메시지 수")
    msg_count = df["User"].value_counts()
    st.bar_chart(msg_count)

    # ---------------------------
    # 응답 시간 분석
    # ---------------------------
    df["PrevDate"] = df["Date"].shift(1)
    df["PrevUser"] = df["User"].shift(1)
    df["ResponseTime"] = (df["Date"] - df["PrevDate"]).dt.total_seconds()

    response_df = df[df["User"] != df["PrevUser"]]
    avg_response = response_df.groupby("User")["ResponseTime"].mean()

    st.subheader("⏱ 평균 응답 시간(초)")
    st.write(avg_response)

    # ---------------------------
    # 친밀도 지수 계산
    # ---------------------------
    edges = []
    for i in range(1, len(df)):
        prev_user = df.iloc[i-1]["User"]
        curr_user = df.iloc[i]["User"]
        if prev_user != curr_user:
            edges.append((prev_user, curr_user))

    relationship_score = []
    for (u1, u2) in set(edges):
        interaction_count = edges.count((u1, u2)) + edges.count((u2, u1))
        resp_times = response_df[
            ((response_df["User"] == u1) & (response_df["PrevUser"] == u2)) |
            ((response_df["User"] == u2) & (response_df["PrevUser"] == u1))
        ]["ResponseTime"]

        if len(resp_times) > 0:
            resp_score = 1 / (resp_times.mean() / 60 + 1)  # 빠를수록 점수 ↑
        else:
            resp_score = 0

        relationship_score.append({
            "User1": u1,
            "User2": u2,
            "Score": round(interaction_count + resp_score, 2)
        })

    st.subheader("💞 친밀도 지수")
    st.dataframe(pd.DataFrame(relationship_score))

    # ---------------------------
    # 이모티콘 비율
    # ---------------------------
    df["IsEmoji"] = df["Message"].str.contains("이모티콘|😂|🤣|❤️|👍|ㅠㅠ|ㅎㅎ|ㅋ")
    emoji_ratio = df.groupby("User")["IsEmoji"].mean() * 100

    st.subheader("😀 이모티콘 사용 비율 (%)")
    st.bar_chart(emoji_ratio)

    # ---------------------------
    # 대화 시간대 패턴
    # ---------------------------
    def get_time_period(hour):
        if 5 <= hour < 12:
            return "아침"
        elif 12 <= hour < 18:
            return "점심/오후"
        elif 18 <= hour < 22:
            return "저녁"
        else:
            return "밤"

    df["Period"] = df["Date"].dt.hour.apply(get_time_period)
    time_pattern = df.groupby(["User", "Period"]).size().unstack(fill_value=0)

    st.subheader("🕒 대화 시간대 패턴")
    st.bar_chart(time_pattern)

    # ---------------------------
    # 네트워크 그래프
    # ---------------------------
    st.subheader("🔗 대화 관계 네트워크")

    G = nx.Graph()
    for row in relationship_score:
        G.add_edge(row["User1"], row["User2"], weight=row["Score"])

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(6, 6))

    # 가중치(친밀도 점수)에 따라 선 굵기 반영
    weights = [G[u][v]['weight'] for u, v in G.edges()]
    nx.draw(
        G, pos, with_labels=True,
        node_size=3000, node_color="lightblue", font_size=12,
        width=[w for w in weights]
    )
    labels = nx.get_edge_attributes(G, 'weight')
    labels = {k: round(v, 2) for k, v in labels.items()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

    st.pyplot(plt)
