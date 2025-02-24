import streamlit as st
import random
import playsound

# 뮤지컬 데이터 (예시)
musicals = {
    "The Phantom of the Opera": {"genre": "Romance", "songs": "phantom_of_the_opera.mp3"},
    "Les Misérables": {"genre": "Drama", "songs": "les_miserables.mp3"},
    "Hamilton": {"genre": "History", "songs": "hamilton.mp3"},
}

# Streamlit UI
st.title("뮤지컬 추천 시스템")

# 설문조사: 장르 선택
genre_preference = st.selectbox(
    "어떤 장르의 뮤지컬을 원하시나요?", ["Romance", "Drama", "History"])

# 추천 버튼
if st.button("뮤지컬 추천 받기"):
    matching_musicals = [musical for musical, details in musicals.items(
    ) if details["genre"].lower() == genre_preference.lower()]

    if matching_musicals:
        recommended = random.choice(matching_musicals)
        st.write(f"추천 뮤지컬: {recommended}")
        st.write("추천된 뮤지컬의 음악을 들려드릴게요!")

        # 음악 재생
        # 음악 파일 경로는 실제 경로로 설정해야 함
        playsound.playsound(musicals[recommended]["songs"])
    else:
        st.write("선택하신 장르에 맞는 뮤지컬이 없습니다.")
