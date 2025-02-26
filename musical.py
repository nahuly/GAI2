import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from youtubesearchpython import VideosSearch

# 뮤지컬 데이터 예제 (뮤지컬 제목, 키워드, 감정 분위기)
musical_data = pd.DataFrame({
    'title': ['Dear Evan Hansen', 'Hamilton', 'Les Misérables', 'Wicked'],
    'keywords': [
        '감동적인, 성장, 청소년, 우정',
        '역사, 랩, 혁명, 미국',
        '전쟁, 감동적인, 희생, 프랑스',
        '마법, 판타지, 여성, 우정'
    ]
})


def recommend_musical(user_input):
    # TF-IDF 벡터화
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(
        musical_data['keywords'].tolist() + [user_input])

    # 코사인 유사도 계산
    cos_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

    # 가장 유사한 뮤지컬 추천
    recommended_idx = cos_sim.argsort()[0][-1]
    recommended_musical = musical_data.iloc[recommended_idx]['title']
    return recommended_musical


def search_musical_song(musical_name):
    search_query = f"{musical_name} official soundtrack"
    search = VideosSearch(search_query, limit=1)
    return search.result()['result'][0]['link']


# Streamlit UI 구성
st.title("🎭 AI 뮤지컬 추천 시스템")
st.write("사용자의 취향을 입력하면 AI가 맞춤형 뮤지컬을 추천해줍니다!")

# 사용자 입력
user_input = st.text_input("🎤 원하는 분위기나 키워드를 입력하세요:",
                           "라라랜드 같은 분위기의 감성적이고 감동적인 성장 이야기")

if st.button("추천 받기"):
    recommended_musical = recommend_musical(user_input)
    song_link = search_musical_song(recommended_musical)

    st.success(f"🎭 추천 뮤지컬: {recommended_musical}")
    st.markdown(f"[🎵 대표곡 듣기]({song_link})")
