import streamlit as st
import pandas as pd
from PIL import Image

# 데이터 로드


@st.cache_data
def load_data():
    file_path = 'ever.csv'
    spirits_data = pd.read_csv(file_path)
    spirits_data_cleaned = spirits_data.dropna().T
    spirits_data_cleaned.columns = spirits_data_cleaned.iloc[0]
    return spirits_data_cleaned.drop(spirits_data_cleaned.index[0])
    # return spirits_data

# 이미지 로드 함수


def load_spirit_image(spirit_name):
    try:
        return Image.open(f"{spirit_name}.png")
    except FileNotFoundError:
        return None


data = load_data()
# st.write(data)

# 웹사이트 제목
st.title("당신의 최애 정령 찾기")

# 질문 및 선택지 설정
questions = {
    "당신이 선호하는 신장은?": data['신장'].unique().tolist(),
    "어떤 취미를 가진 정령을 좋아하시나요?": data['취미'].unique().tolist(),
    "어떤 특기를 가진 정령을 선호하시나요?": data['특기'].unique().tolist(),
    "정령이 좋아하는 것 중 당신의 취향과 맞는 것은?": data['좋아하는 것'].unique().tolist(),
    "어떤 색상의 정령을 선호하시나요?": data['캐릭터 색상'].unique().tolist()
}

# st.write(data)
# st.write(data['name'])
# st.write(data['소속'].unique().tolist())
# st.write(data.loc[data['name'] == '제이드', '신장'].values[0])

# 사용자 응답 저장
responses = {}

# 질문 표시 및 응답 수집
for question, options in questions.items():
    response = st.selectbox(question, options)
    responses[question] = response

# 결과 계산 버튼
if st.button("결과 보기"):
    scores = {spirit: 0 for spirit in data['name']}

    for question, response in responses.items():
        for spirit in data['name']:
            if question == "당신이 선호하는 신장은?":
                if response == data.loc[data['name'] == spirit, '신장'].values[0]:
                    scores[spirit] += 1
            elif question == "어떤 취미를 가진 정령을 좋아하시나요?":
                if response == data.loc[data['name'] == spirit, '취미'].values[0]:
                    scores[spirit] += 1
            elif question == "어떤 특기를 가진 정령을 선호하시나요?":
                if response == data.loc[data['name'] == spirit, '특기'].values[0]:
                    scores[spirit] += 1
            elif question == "정령이 좋아하는 것 중 당신의 취향과 맞는 것은?":
                if response == data.loc[data['name'] == spirit, '좋아하는 것'].values[0]:
                    scores[spirit] += 1
            elif question == "어떤 색상의 정령을 선호하시나요?":
                if response.lower() == data.loc[data['name'] == spirit, '캐릭터 색상'].values[0].lower():
                    scores[spirit] += 1

    st.write(scores)

    # 점수에 따라 정령 정렬
    ranked_spirits = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    st.write(ranked_spirits)

    # # 결과 표시
    # st.subheader("당신의 최애 정령 순위:")
    # for rank, (spirit, score) in enumerate(ranked_spirits[:3], 1):
    #     st.write(f"{rank}위: {spirit}")
    #     st.write(f"소속: {data.loc[data['name'] == spirit, 'team'].values[0]}")
    #     st.write(f"특기: {data.loc[data['name'] == spirit, '특기'].values[0]}")
    #     st.write(f"취미: {data.loc[data['name'] == spirit, '취미'].values[0]}")
    #     st.write("---")

    # 결과 표시
    st.subheader("당신의 최애 정령 순위:")
    for rank, (spirit, score) in enumerate(ranked_spirits[:3], 1):
        col1, col2 = st.columns([1, 3])

        with col1:
            image = load_spirit_image(spirit)
            if image:
                st.image(image, caption=spirit, use_column_width=True)
            else:
                st.write("이미지 없음")

        with col2:
            st.subheader(f"{rank}위: {spirit}")
            st.write(
                f"소속: {data.loc[data['name'] == spirit, '소속'].values[0]}")
            st.write(f"특기: {data.loc[data['name'] == spirit, '특기'].values[0]}")
            st.write(f"취미: {data.loc[data['name'] == spirit, '취미'].values[0]}")

        st.write("---")
