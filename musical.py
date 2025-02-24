import random
import streamlit as st

# SM 아티스트와 대표곡
sm_artists = {
    "TVXQ": ["Mirotic", "Catch Me", "Rising Sun"],
    "SUPER JUNIOR": ["Sorry, Sorry", "Mr. Simple", "U"],
    "EXO": ["Growl", "Call Me Baby", "Love Shot"],
    "Red Velvet": ["Bad Boy", "Psycho", "Red Flavor"],
    "NCT": ["Kick Back", "Cherry Bomb", "Make A Wish"],
}

# Streamlit UI
st.title("SM 30주년 기념 노래 추천")

# 아티스트 선택
artist_choice = st.selectbox(
    "어떤 SM 아티스트의 노래를 추천받고 싶으세요?", list(sm_artists.keys()))

# 추천 버튼
if st.button("노래 추천 받기"):
    recommended_song = random.choice(sm_artists[artist_choice])
    st.write(f"{artist_choice}의 추천 노래: {recommended_song}")
