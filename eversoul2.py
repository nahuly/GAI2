import streamlit as st
import pandas as pd
from PIL import Image

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


# 페이지 설정
st.set_page_config(layout="wide", page_title="Soulmate 정령 찾기")


# CSS 스타일 정의
st.markdown("""
    <style>
    .title {
        font-size: 60px !important;  /* 원하는 크기로 조정 */
        color: #1E90FF;               /* 제목 색상 */
        text-align: center;           /* 중앙 정렬 */
        text-shadow: 2px 2px 4px #CCE5FF; /* 그림자 효과 */
    }
    </style>
    """, unsafe_allow_html=True)

# 제목 표시
st.markdown('<p class="title">Soulmate 정령 찾기</p>', unsafe_allow_html=True)

# 취미, 특기, 좋아하는 것, 싫어하는 것을 5가지 범주로 분류
type_categories = {
    "평범한 인간 형태의 정령이 좋다": ["인간형"],
    "동물 귀와 꼬리가 포인트인 정령이 좋다": ["야수형"],
    "요정 특유의 귀가 포인트인 정령이 좋다": ["요정형"],
    "언데드 또는 기계 계열(전체적으로 창백)이 좋다": ["불사형"],
    "천사형(악마형과 함께 가장 강력한 타입)이 좋다": ["천사형"],
    "악마형(천사형과 함께 가장 강력한 타입)이 좋다": ["악마형"]
}

hobby_categories = {
    "예술/창의적 활동이 나랑 맞다": ["그림 그리기", "초상화 그리기", "패밀리어 상대 탐색", "작은 나사 수집"],
    "자연/야외 활동같이 활발한게 나랑 맞다": ["별 보기", "원예, 검수집", "구름 빗어주기", "산책, 정원 손질"],
    "음식/요리하는 것처럼 정적인게 좋다": ["과자 굽기", "도시락 만들기", "커피 우유 만들기"],
    "수집/관찰처럼 뭔가를 분석하고 모으는게 좋다": ["고양이 관찰", "보석 관리", "마리모 키우기", "입욕제 모으기"],
    "운동/체육 활동처럼 움직여야 한다!": ["검무", "제기 차기", "심호흡, 수영"]
}

skill_categories = {
    "조용히 분석하거나 전문성이 있는 정령이 좋다": ["데이터 분석", "정보 수집", "분석, 회유"],
    "사람들 앞에서 연설하거나 설교하는 정령이 좋다": ["큰소리로 연설하기", "설교", "온화한 미소 짓기"],
    "운동이나 전투처럼 격한게 좋다": ["검무", "힘 쓰기", "도망치기"],
    "창의적이거나 예술적인 활동이 나랑 맞다": ["연기", "애교 섞인 비음", "멋진 포즈 연구"],
    "다른 사람들 도와주거나 보조적인 역할을 해주는 정령이 좋다": ["자가 정비", "위치 추적", "땅 파기, 어둠 속에서 길 찾기"]
}

like_categories = {
    "당연히 음식이 먼저지!": ["케이크", "부추빵", "오렌지 맛 사탕", "커피 우유", "포츈 쿠키"],
    "당연히 자연과 동물을 좋아해야지!": ["꽃", "별님", "강아지", "정령들의 미소"],
    "당연히 사물이나 수집하는 것을 좋아해야하는거 아님?": ["반짝이는 것", "캐럿", "스티커"],
    "당연히 행사나 축제 보러 다니는게 최고임!": ["축제 구경", "연애 소설", "소원 부적"],
    "당연히 실용적인 기능성 물품이 최고다": ["기능성 오일", "니삭스", "컵라면"]
}

dislike_categories = {
    "음식 싫어하는 게 대표적이지...": ["마요네즈", "오트밀 죽", "생선 회", "한약", "민트류 음식"],
    "실패하거나 제어 불능 상황이 오는게 제일 싫어!": ["오류", "통제 불가능한 상황", "외로움", "실수하는 것"],
    "강요나 구속은 최악이야!": ["구속", "강요", "하극상"],
    "청결하지 못하거나 혼란스러운 건 참을 수 없어...": ["지저분함", "채무 불이행", "불필요한 소비"],
    "범죄나 악행을 저지르는 것이 제일 최악이야": ["범죄", "악인", "다혈질"]
}

# 페이지 설정 (항상 스크립트의 맨 위에 위치해야 함)
# st.set_page_config(layout="wide", page_title="Soulmate 정령 찾기")


# 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 0

if 'choices' not in st.session_state:
    st.session_state.choices = {}


# 각 단계별 질문 함수
def ask_question(question, options, key):
    choice = st.radio(question, options)
    if st.button("다음", key=f"next_{key}"):
        st.session_state.choices[key] = choice
        st.session_state.step += 1
        st.rerun()


# 이미지 로드 함수
def load_spirit_image(spirit_name):
    try:
        return Image.open(f"eversoul_image/{spirit_name}.png")
    except FileNotFoundError:
        return None


# 결과 표시 함수
def show_results():
    # 점수 계산 로직 (기존 코드와 동일)
    df['점수'] = 0

    for type in type_categories[st.session_state.choices['type']]:
        df.loc[df['타입'].str.contains(type), '점수'] += 1

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
    # st.write(top3)

    st.subheader("당신과 잘 맞는 상위 3명의 소울메이트 정령:")
    # for i, row in top3.iterrows():
    #     st.write(f"{i}위: {row['이름']} (점수: {row['점수']})")
    for i, row in top3.iterrows():
        col1, col2 = st.columns([3, 2])  # 3:2 비율로 컬럼 분할
        spirit = row['이름']

        with col1:
            image = load_spirit_image(spirit)
            if image:
                st.image(image, caption=spirit, use_column_width=True)
            else:
                st.write("이미지 없음")

        with col2:
            st.markdown(f"**{i}위: {row['이름']}**")
            st.markdown(f"**타입:** {row['타입']}")
            st.markdown(f"**취미:** {row['취미']}")
            st.markdown(f"**특기:** {row['특기']}")
            st.markdown(f"**좋아하는 것:** {row['좋아하는 것']}")
            st.markdown(f"**싫어하는 것:** {row['싫어하는 것']}")

        st.write("---")


# # 단계별 질문 표시
# if st.session_state.step == 0:
#     ask_question("가장 좋아하는 취미를 선택하세요:", list(hobby_categories.keys()), 'hobby')
# elif st.session_state.step == 1:
#     ask_question("가장 뛰어난 특기를 선택하세요:", list(skill_categories.keys()), 'skill')
# elif st.session_state.step == 2:
#     ask_question("가장 좋아하는 것을 선택하세요:", list(like_categories.keys()), 'like')
# elif st.session_state.step == 3:
#     ask_question("가장 싫어하는 것을 선택하세요:", list(
#         dislike_categories.keys()), 'dislike')
# elif st.session_state.step == 4:
#     show_results()
#     if st.button("처음부터 다시하기"):
#         st.session_state.step = 0
#         st.session_state.choices = {}
#         st.rerun()


# 단계별 질문 표시
if st.session_state.step == 0:
    # 이미지 로드 (이미지 파일의 경로를 적절히 수정하세요)
    image = Image.open("eversoul_image/ever_title.png")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.image(image, use_column_width=True)
        st.markdown(
            '<p class="subtitle">당신의 운명적인 소울메이트 정령을<br>지금 바로 찾아보세요!</p>', unsafe_allow_html=True)

    # 중앙 정렬을 위한 컬럼 사용
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✨ 시작하기 ✨", key="start_button"):
            st.session_state.step += 1
            st.rerun()
elif st.session_state.step == 1:
    ask_question("당신이 좋아하는 타입은?:", list(type_categories.keys()), 'type')
elif st.session_state.step == 2:
    ask_question("가장 좋아하는 취미를 선택하세요:", list(hobby_categories.keys()), 'hobby')
elif st.session_state.step == 3:
    ask_question("가장 뛰어난 특기를 선택하세요:", list(skill_categories.keys()), 'skill')
elif st.session_state.step == 4:
    ask_question("가장 좋아하는 것을 선택하세요:", list(like_categories.keys()), 'like')
elif st.session_state.step == 5:
    ask_question("가장 싫어하는 것을 선택하세요:", list(
        dislike_categories.keys()), 'dislike')
elif st.session_state.step == 6:
    show_results()
    if st.button("처음부터 다시하기"):
        st.session_state.step = 0
        st.session_state.choices = {}
        st.rerun()
