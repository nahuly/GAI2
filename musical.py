import datetime
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 뮤지컬 데이터 예제 (뮤지컬 제목, 키워드, 감정 분위기)
musical_data = pd.DataFrame({
    'title': [
        'Dear Evan Hansen', 'Hamilton', 'Les Misérables', 'Wicked', 'The Phantom of the Opera',
        'The Lion King', 'Mamma Mia!', 'Les Misérables', 'Rent', 'Cats',
        'Aladdin', 'Frozen', 'The Book of Mormon', 'Chicago', 'Hairspray',
        'The Sound of Music', 'West Side Story', 'Waitress', 'Hadestown', 'The Greatest Showman'
    ],
    'keywords': [
        '감동적인, 성장, 청소년, 우정',
        '역사, 랩, 혁명, 미국',
        '전쟁, 감동적인, 희생, 프랑스',
        '마법, 판타지, 여성, 우정',
        '고딕, 사랑, 미스터리, 음악',
        '애니메이션, 가족, 동물, 사랑',
        '여성, 우정, 디스코, 팝',
        '전쟁, 감동적인, 희생, 프랑스',
        '감동적인, 청춘, 사랑, 사회적 이슈',
        '뮤지컬, 사랑, 우정, 파티',
        '동물, 사랑, 자유, 가족',
        '마법, 알라딘, 모험, 사랑',
        '겨울, 사랑, 마법, 우정',
        '모험, 종교, 혁명, 남북전쟁',
        '범죄, 로맨스, 브로드웨이, 춤',
        '가족, 사랑, 사회적 메시지',
        '음악, 사랑, 가족, 사회적 이슈',
        '로맨스, 청춘, 갈등, 사랑',
        '음악, 사랑, 신화, 현대',
        '모험, 서커스, 로맨스, 노래'
    ]
})

# 뮤지컬별 추천 곡 TOP3 (예시)
musical_songs = {
    'Dear Evan Hansen': [
        'You Will Be Found',
        'Waving Through a Window',
        'For Forever'
    ],
    'Hamilton': [
        'My Shot',
        'The Room Where It Happens',
        'Wait For It'
    ],
    'Les Misérables': [
        'I Dreamed a Dream',
        'On My Own',
        'Do You Hear the People Sing?'
    ],
    'Wicked': [
        'Defying Gravity',
        'Popular',
        'For Good'
    ],
    'The Phantom of the Opera': [
        'The Phantom of the Opera',
        'Music of the Night',
        'All I Ask of You'
    ],
    'The Lion King': [
        'Circle of Life',
        'Hakuna Matata',
        'Can You Feel the Love Tonight'
    ],
    'Mamma Mia!': [
        'Dancing Queen',
        'Mamma Mia',
        'Take a Chance on Me'
    ],
    'Les Misérables': [
        'I Dreamed a Dream',
        'On My Own',
        'Do You Hear the People Sing?'
    ],
    'Rent': [
        'Seasons of Love',
        'La Vie Boheme',
        'One Song Glory'
    ],
    'Cats': [
        'Memory',
        'Jellicle Songs for Jellicle Cats',
        'Mr. Mistoffelees'
    ],
    'Aladdin': [
        'A Whole New World',
        'Friend Like Me',
        'Prince Ali'
    ],
    'Frozen': [
        'Let It Go',
        'Do You Want to Build a Snowman?',
        'For the First Time in Forever'
    ],
    'The Book of Mormon': [
        'I Believe',
        'Hasa Diga Eebowai',
        'Turn It Off'
    ],
    'Chicago': [
        'All That Jazz',
        'Cell Block Tango',
        'Razzle Dazzle'
    ],
    'Hairspray': [
        'Good Morning Baltimore',
        'You Can’t Stop the Beat',
        'I Know Where I’ve Been'
    ],
    'The Sound of Music': [
        'Do-Re-Mi',
        'My Favorite Things',
        'Climb Every Mountain'
    ],
    'West Side Story': [
        'Tonight',
        'America',
        'Somewhere'
    ],
    'Waitress': [
        'She Used to Be Mine',
        'Sugar, Butter, Flour',
        'What Baking Can Do'
    ],
    'Hadestown': [
        'Road to Hell',
        'Hey, Little Songbird',
        'Why We Build the Wall'
    ],
    'The Greatest Showman': [
        'This Is Me',
        'The Greatest Show',
        'Rewrite the Stars'
    ]
}

# 각 뮤지컬에 맞는 로컬 이미지 경로
musical_icons = {
    'Dear Evan Hansen': 'images/Dear.png',  # Dear Evan Hansen 이미지
    'Hamilton': 'images/Hamilton.png',  # Hamilton 이미지
    'Les Misérables': 'images/Les.png',  # Les Misérables 이미지
    'Wicked': 'images/wicked.png',  # Wicked 이미지
    'The Phantom of the Opera': 'images/Phantom.png',
    'The Lion King': 'images/Lion.png',  # The Lion King 이미지
    'Les Misérables': 'images/Les.png',  # The Lion King 이미지
    'Mamma Mia!': 'images/Mamma.png',  # Mamma Mia! 이미지
    'Rent': 'images/Rent.png',  # Rent 이미지
    'Cats': 'images/Cats.png',  # Cats 이미지
    'Aladdin': 'images/Aladdin.png',  # Aladdin 이미지
    'Frozen': 'images/Frozen.png',  # Frozen 이미지
    'The Book of Mormon': 'images/Mormon.png',  # The Book of Mormon 이미지
    'Chicago': 'images/Chicago.png',  # Chicago 이미지
    'Hairspray': 'images/Hairspray.png',  # Hairspray 이미지
    'The Sound of Music': 'images/Sound.png',  # The Sound of Music 이미지
    'West Side Story': 'images/West.png',  # West Side Story 이미지
    'Waitress': 'images/Waitress.png',  # Waitress 이미지
    'Hadestown': 'images/Hadestown.png',  # Hadestown 이미지
    'The Greatest Showman': 'images/Greatest.png',  # The Greatest Showman 이미지
}

# Streamlit UI 구성
st.title("🎭 AI 뮤지컬 추천 시스템")
st.write("사용자의 취향을 입력하면 AI가 맞춤형 뮤지컬을 추천해줍니다!")

# 사용자 입력 (기분, 키워드)
user_input = st.text_input("🎤 원하는 분위기나 키워드를 입력하세요:",
                           "라라랜드 같은 분위기의 감성적이고 감동적인 성장 이야기")

# TF-IDF 벡터화 및 코사인 유사도 계산
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(
    musical_data['keywords'].tolist() + [user_input])

cos_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

# 가장 유사한 뮤지컬 추천
recommended_idx = cos_sim.argsort()[0][-1]
recommended_musical = musical_data.iloc[recommended_idx]['title']

# 추천된 뮤지컬 아이콘 표시 (로컬 이미지)
st.image(musical_icons.get(recommended_musical, 'images/default.png'), width=150)
st.write(f"🎭 추천 뮤지컬: {recommended_musical}")

# YouTube에서 뮤지컬 대표곡 검색 함수 (웹 크롤링 사용)


def search_musical_song(musical_name):
    search_query = f"{musical_name} official soundtrack"
    search_url = f"https://www.youtube.com/results?search_query={search_query}"

    # YouTube 페이지 요청
    response = requests.get(search_url)

    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(response.text, 'html.parser')

    # 첫 번째 비디오 링크 추출
    video_id = soup.find('a', {'href': True})['href']
    return f"https://www.youtube.com{video_id}"


# 추천된 뮤지컬 넘버 검색
song_link = search_musical_song(recommended_musical)
st.write(f"🎵 {recommended_musical} 대표곡 듣기: [링크]({song_link})")

# 뮤린이가 듣기 좋은 곡 TOP3 표시
st.write("🎶 뮤린이가 듣기 좋은 곡 추천 TOP3:")
for idx, song in enumerate(musical_songs[recommended_musical], 1):
    st.write(f"{idx}. {song}")

# 타이틀
st.markdown(
    """
    <div style="text-align: center;">
        <h1 style="font-size: 32px;">🎭 뮤지컬 많.관.부!!!</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# 현재 날짜
today = datetime.date.today()

# 공연 정보
musicals = [
    {"title": "지킬앤하이드 20주년", "end_date": "2025-05-18", "venue": "블루스퀘어 신한카드홀"},
    {"title": "알라딘 초연", "end_date": "2025-06-22", "venue": "샤롯데씨어터"},
    {"title": "명성황후 30주년", "end_date": "2025-03-30", "venue": "세종문화회관 대극장"},
    {"title": "웃는남자", "end_date": "2025-03-09", "venue": "예술의전당 오페라극장"},
    {"title": "베르테르 25주년", "end_date": "2025-03-16", "venue": "디큐브 링크아트센터"},
    {"title": "마타하리", "end_date": "2025-03-02", "venue": "LG아트센터 서울"},
]

# 현재 공연 중인 뮤지컬 필터링
ongoing_musicals = [
    musical for musical in musicals if datetime.date.fromisoformat(musical["end_date"]) >= today
]

# 공연 리스트 출력
st.markdown("<h2 style='font-size: 24px; text-align: center;'>🎶 현재 공연 중인 뮤지컬 추천!</h2>",
            unsafe_allow_html=True)

if ongoing_musicals:
    for musical in ongoing_musicals:
        st.markdown(
            f"""
            <div style="font-size: 16px; line-height: 1.6; text-align: center;">
                <strong>🎭 {musical['title']}</strong>  <br>
                📍 장소: {musical['venue']}  <br>
                📅 공연 종료: {musical['end_date']}  
                <hr>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.markdown("<p style='font-size: 16px; text-align: center;'>현재 공연 중인 뮤지컬이 없습니다. 😢</p>",
                unsafe_allow_html=True)
