import streamlit as st
import pandas as pd

# 데이터 로드
data = {
    "이름": ["메피스토텔레스", "제이드", "린지", "캐서린", "아키", "미카", "시하", "홍란", "순이", "사쿠요", "탈리아", "비비안", "마농", "다프네", "도미니크", "재클린", "페트라", "비올레트", "가넷", "시그리드", "아드리안", "클라우디아", "유리아", "아야메", "리젤로테", "이브", "라리마"],
    "타입": ["인간형", "인간형", "인간형", "인간형", "인간형", "야수형", "야수형", "야수형", "야수형", "야수형", "요정형", "요정형", "요정형", "요정형", "요정형", "불사형", "불사형", "불사형", "불사형", "불사형", "천사형", "천사형", "천사형", "악마형", "악마형", "악마형", "악마형"],
    "취미": ["고양이 관찰", "보석 관리", "풍경 감상, 높은 곳", "과자 굽기", "입욕제 모으기", "사인 연습", "마리모 키우기", "구름 빗어주기", "공기놀이, 체통 지키기", "원예, 검수집", "초상화 그리기 (안 닮음)", "패밀리어 상대 탐색", "도시락 만들기", "별 보기", "그림 그리기", "작은 나사 수집", "멍하니 있기, 빛나는 것 모으기", "귀염둥이(구원자) 괴롭히기", "캐럿 꾸미기", "정보 수집", "영지 순찰", "복화술", "산책, 정원 손질", "꽃검 치기", "다림질", "바깥 돌아다니기", "아폴리온 님 숭배"],
    "특기": ["데이터 분석", "정보 수집", "뛰어난 직감", "설교", "검무", "팬 서비스 연구", "심호흡, 수영", "몽상하기", "제기 차기", "큰소리로 연설하기", "신통방통 별점", "빗자루 만취 운전", "속셈", "힘 쓰기", "도망치기", "자가 정비", "땅 파기, 어둠 속에서 길 찾기", "애교 섞인 비음", "위치 추적", "절대미각", "멋진 포즈 연구", "온화한 미소 짓기", "매운 음식 먹기", "매듭 공예", "연기", "분석, 회유", "정치 공작"],
    "좋아하는 것": ["케이크", "꽃", "백합, 허브티", "따끈한 포토푀", "연애 소설", "오렌지 맛 사탕", "부추빵", "구름 과자", "약과, 감주", "사탕, 나비", "별님, 포츈 쿠키", "시원한 맥주", "커피 우유, 애착 담요", "축제 구경, 멋진 만남", "스티커, 도마뱀, 쓴맛", "기능성 오일", "반짝이는 것, 장난", "구속, 복종", "캐럿, 니삭스", "자신이 모르는 것, 비밀", "강아지, 감동 실화", "밀크티", "정령들의 미소", "소원 부적", "컵라면", "실험, 논리적인 결론", "종말십자회"],
    "싫어하는 것": ["오류, 통제 불가능한 상황", "기만", "마요네즈", "오트밀 죽", "민트류 음식", "공부", "생선 회", "우박 (맞으면 아프다)", "한약", "하극상, 쓴맛", "어린애 취급", "청소, 숙취", "장기 연체, 채무 불이행, 불필요한 소비", "외로움, 실수하는 것", "발표, 연설", "결함, 고장", "구속, 강요", "바람둥이", "지저분함, 통제 불능", "상식", "범죄, 악인", "다혈질", "약자의 희생", "하얀 꽃", "장시간 외출", "맹목", "영원, 외부의 적"]
}

# 정령 데이터를 pandas DataFrame으로 변환
df = pd.DataFrame(data)

# Streamlit 앱 설정
st.title('Soulmate 정령 찾기')

# 취미, 특기, 좋아하는 것, 싫어하는 것을 5가지 범주로 분류
hobby_categories = {
    "예술/창의적 활동": ["그림 그리기", "초상화 그리기", "패밀리어 상대 탐색", "작은 나사 수집"],
    "자연/야외 활동": ["별 보기", "원예, 검수집", "구름 빗어주기", "산책, 정원 손질"],
    "음식/요리": ["과자 굽기", "도시락 만들기", "커피 우유 만들기"],
    "수집/관찰": ["고양이 관찰", "보석 관리", "마리모 키우기", "입욕제 모으기"],
    "운동/체육 활동": ["검무", "제기 차기", "심호흡, 수영"]
}

skill_categories = {
    "분석/전문성": ["데이터 분석", "정보 수집", "분석, 회유"],
    "연설/설교": ["큰소리로 연설하기", "설교", "온화한 미소 짓기"],
    "운동/전투": ["검무", "힘 쓰기", "도망치기"],
    "예술/창의적": ["연기", "애교 섞인 비음", "멋진 포즈 연구"],
    "도움/치유": ["자가 정비", "위치 추적", "땅 파기, 어둠 속에서 길 찾기"]
}

like_categories = {
    "음식": ["케이크", "부추빵", "오렌지 맛 사탕", "커피 우유", "포츈 쿠키"],
    "자연/동물": ["꽃", "별님", "강아지", "정령들의 미소"],
    "사물/수집": ["반짝이는 것", "캐럿", "스티커"],
    "행사/축제": ["축제 구경", "연애 소설", "소원 부적"],
    "기능성 물품": ["기능성 오일", "니삭스", "컵라면"]
}

dislike_categories = {
    "음식": ["마요네즈", "오트밀 죽", "생선 회", "한약", "민트류 음식"],
    "실패/제어 불능": ["오류", "통제 불가능한 상황", "외로움", "실수하는 것"],
    "강요/구속": ["구속", "강요", "하극상"],
    "불청결/혼란": ["지저분함", "채무 불이행", "불필요한 소비"],
    "범죄/악행": ["범죄", "악인", "다혈질"]
}


# 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 0

if 'choices' not in st.session_state:
    st.session_state.choices = {}

# Streamlit 앱 설정
st.title('Soulmate 정령 찾기')

# 각 단계별 질문 함수


def ask_question(question, options, key):
    choice = st.selectbox(question, options)
    if st.button("다음", key=f"next_{key}"):
        st.session_state.choices[key] = choice
        st.session_state.step += 1
        st.rerun()

# 결과 표시 함수


def show_results():
    # 점수 계산 로직 (기존 코드와 동일)
    df['점수'] = 0

    for hobby in hobby_categories[st.session_state.choices['hobby']]:
        df.loc[df['취미'].str.contains(hobby), '점수'] += 1

    for skill in skill_categories[st.session_state.choices['skill']]:
        df.loc[df['특기'].str.contains(skill), '점수'] += 1

    for like in like_categories[st.session_state.choices['like']]:
        df.loc[df['좋아하는 것'].str.contains(like), '점수'] += 1

    for dislike in dislike_categories[st.session_state.choices['dislike']]:
        df.loc[df['싫어하는 것'].str.contains(dislike) == False, '점수'] += 1

    top3 = df.sort_values(by='점수', ascending=False).head(
        3).reset_index(drop=True)
    top3.index = [1, 2, 3]
    st.write(top3)

    st.subheader("당신과 잘 맞는 상위 3명의 소울메이트 정령:")
    for i, row in top3.iterrows():
        st.write(f"{i+1}위: {row['이름']} (점수: {row['점수']})")


# 단계별 질문 표시
if st.session_state.step == 0:
    ask_question("가장 좋아하는 취미를 선택하세요:", list(hobby_categories.keys()), 'hobby')
elif st.session_state.step == 1:
    ask_question("가장 뛰어난 특기를 선택하세요:", list(skill_categories.keys()), 'skill')
elif st.session_state.step == 2:
    ask_question("가장 좋아하는 것을 선택하세요:", list(like_categories.keys()), 'like')
elif st.session_state.step == 3:
    ask_question("가장 싫어하는 것을 선택하세요:", list(
        dislike_categories.keys()), 'dislike')
elif st.session_state.step == 4:
    show_results()
    if st.button("처음부터 다시하기"):
        st.session_state.step = 0
        st.session_state.choices = {}
        st.rerun()
