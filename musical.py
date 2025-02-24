from sklearn.preprocessing import LabelEncoder
import random
import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# SM 아티스트와 대표곡 데이터 (여기에 장르나 스타일도 추가 가능)
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

# 아티스트 선택
artist_choice = st.selectbox(
    "어떤 SM 아티스트의 노래를 추천받고 싶으세요?", list(sm_artists.keys()))

# 추천 버튼
if st.button("AI 노래 추천 받기"):
    song_list = list(sm_artists[artist_choice].keys())

    # 랜덤 추천 대신 AI 기반 추천
    song_idx = random.randint(0, len(song_list) - 1)
    selected_song = song_list[song_idx]

    st.write(f"추천 노래: {selected_song}")
    st.write("AI 기반 추천입니다!")

    # 유사한 노래 추천
    idx = song_names.index(selected_song)
    similar_songs = cosine_sim[idx]

    # 유사한 노래 3개 추천
    similar_idx = similar_songs.argsort()[-4:-1][::-1]  # 가장 유사한 3곡
    st.write("비슷한 노래들:")
    for idx in similar_idx:
        st.write(song_names[idx])
