import streamlit as st

# 제목
st.title("🎭 뮤지컬 예매 정보")

# 사용자 입력
user_input = st.text_input("검색할 뮤지컬 이름을 입력하세요:")

# 버튼 추가
if st.button("검색하기"):
    if user_input:
        st.success(f"🎟️ '{user_input}' 관련 정보를 검색 중...")
    else:
        st.warning("❗ 뮤지컬 이름을 입력하세요!")

# 예제 정보 출력
st.subheader("🔥 이번 주 추천 뮤지컬")
st.write("📌 **뮤지컬 '레미제라블'** - 티켓팅: 3월 20일 (수)")
st.write("📌 **뮤지컬 '위키드'** - 티켓팅: 3월 22일 (금)")
st.write("📌 **뮤지컬 '라이온 킹'** - 티켓팅: 3월 25일 (월)")
