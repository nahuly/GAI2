import streamlit as st
import pandas as pd

# 데이터 로드


@st.cache_data
def load_data():
    file_path = 'ever.csv'
    spirits_data = pd.read_csv(file_path)
    spirits_data_cleaned = spirits_data.dropna().T
    spirits_data_cleaned.columns = spirits_data_cleaned.iloc[0]
    return spirits_data_cleaned.drop(spirits_data_cleaned.index[0])


data = load_data()


def main():
    st.title("당신의 최애 정령 찾기")

    # 세션 상태 초기화
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    if 'results' not in st.session_state:
        st.session_state.results = None

    st.write(data)
    st.write(data['name'])

    # 질문 및 선택지 설정
    questions = {
        "당신이 선호하는 신장은?": ["155cm", "167cm"],
        "어떤 취미를 가진 정령을 좋아하시나요?": ["고양이 관찰", "보석 관리"],
        "어떤 특기를 가진 정령을 선호하시나요?": ["데이터 분석", "정보 수집"],
        "정령이 좋아하는 것 중 당신의 취향과 맞는 것은?": ["케이크", "꽃"],
        "어떤 색상의 정령을 선호하시나요?": ["#F5F1EB", "#8F735E"]
    }

    st.write(questions)

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

        # 점수에 따라 정령 정렬
        st.session_state.results = sorted(
            scores.items(), key=lambda x: x[1], reverse=True)

        # 결과 페이지로 이동
        st.rerun()


if __name__ == "__main__":
    main()
