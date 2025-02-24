import random
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder

# SM 아티스트와 대표곡 데이터 (장르, 템포, 분위기 포함)
sm_artists = {
    "TVXQ": {"Mirotic": {"genre": "Pop", "tempo": "Fast", "mood": "Energetic"},
             "Catch Me": {"genre": "Pop", "tempo": "Fast", "mood": "Energetic"}},
    "SUPER JUNIOR": {"Sorry, Sorry": {"genre": "Dance", "tempo": "Fast", "mood": "Fun"},
                     "Mr. Simple": {"genre": "Dance", "tempo": "Fast", "mood": "Fun"}},
    "EXO": {"Growl": {"genre": "Pop", "tempo": "Medium", "mood": "Cool"},
            "Call Me Baby": {"genre": "Pop", "tempo": "Fast", "mood": "Energetic"}},
    "Red Velvet": {"Bad Boy": {"genre": "R&B", "tempo": "Medium", "mood": "Sexy"},
                   "Psycho": {"genre": "Pop", "tempo": "Slow", "mood": "Romantic"}},
    "NCT": {"Kick Back": {"genre": "Pop", "tempo": "Fast", "mood": "Energetic"},
            "Cherry Bomb": {"genre": "Dance", "tempo": "Fast", "mood": "Fun"}}
}

# 곡들의 특성 벡터 만들기
songs = []
song_names = []
for artist, songs_data in sm_artists.items():
    for song, features in songs_data.items():
        song_names.append(song)
        songs.append([features["genre"], features["tempo"], features["mood"]])

# 특성 벡터를 수치화
encoder = LabelEncoder()
songs_encoded = []
for song in songs:
    songs_encoded.append([encoder.fit_transform([feature])[0]
                         for feature in song])

# 코사인 유사도 계산
cosine_sim = cosine_similarity(songs_encoded)

# Streamlit UI
st.title("SM 30주년 기념 AI 노래 추천 시스템")

# 사용자에게 여러 가지 질문 던지기
genre_choice = st.selectbox(
    "원하는 장르를 선택하세요:", ["Pop", "Dance", "R&B", "Hip-Hop", "Ballad"])
tempo_choice = st.selectbox("원하는 템포를 선택하세요:", ["Fast", "Medium", "Slow"])
mood_choice = st.selectbox(
    "원하는 분위기를 선택하세요:", ["Energetic", "Fun", "Cool", "Sexy", "Romantic"])

# 추천 버튼
if st.button("AI 노래 추천 받기"):
    filtered_songs = []

    # 선택한 장르, 템포, 분위기에 맞는 곡을 필터링
    for i, song in enumerate(songs):
        if song[0] == genre_choice and song[1] == tempo_choice and song[2] == mood_choice:
            filtered_songs.append(song_names[i])

    if filtered_songs:
        st.write(
            f"추천 노래들 (장르: {genre_choice}, 템포: {tempo_choice}, 분위기: {mood_choice}):")
        for song in filtered_songs:
            st.write(song)
    else:
        st.write("선택하신 조건에 맞는 노래가 없습니다. 다른 조건을 선택해 보세요.")

    # Generative AI 느낌을 추가한 부분: 가상의 곡 생성
    if filtered_songs:
        # 선택된 조건에 맞는 새로운 "가상" 곡을 생성
        st.write("AI가 생성한 새로운 곡 추천:")

        # AI가 생성한 가상의 곡 특성 (장르, 템포, 분위기 랜덤 조합)
        generated_genre = random.choice([genre_choice, "Pop", "Dance", "R&B"])
        generated_tempo = random.choice(
            [tempo_choice, "Fast", "Slow", "Medium"])
        generated_mood = random.choice(
            [mood_choice, "Energetic", "Fun", "Romantic", "Sexy"])

        # 생성된 가상의 곡 이름
        generated_song = f"AI Generated - {generated_genre} {generated_tempo} {generated_mood}"
        st.write(f"곡 이름: {generated_song}")
        st.write(
            f"장르: {generated_genre}, 템포: {generated_tempo}, 분위기: {generated_mood}")

        # 유사한 노래 추천 (필터링된 노래 중에서)
        random_song = random.choice(filtered_songs)
        st.write(f"선택된 노래: {random_song}")

        idx = song_names.index(random_song)
        similar_songs = cosine_sim[idx]

        # 유사한 노래 3개 추천
        similar_idx = similar_songs.argsort()[-4:-1][::-1]  # 가장 유사한 3곡
        st.write("비슷한 노래들:")
        for idx in similar_idx:
            st.write(song_names[idx])

    # 피드백 받기
    feedback = st.radio("이 추천은 어땠나요?", ["좋아요", "별로에요", "보통이에요"])
    if feedback:
        st.write(f"감사합니다! 피드백: {feedback}")
