from googleapiclient.discovery import build

# API 키 설정 (Google Cloud에서 발급받은 API 키 입력)
api_key = "AIzaSyBhWZeQJp-XcxafgU9q0BmECArbcjlQzuA"

# YouTube API 클라이언트 빌드
youtube = build('youtube', 'v3', developerKey=api_key)

# 비디오 검색 함수


def search_youtube(query):
    # 'search' API를 사용하여 비디오 검색
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=1  # 한 개의 비디오만 검색
    )
    response = request.execute()

    # 비디오 ID 추출
    video_id = response['items'][0]['id']['videoId']

    # YouTube 링크 반환
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    return video_url


# 검색어로 비디오 검색
search_query = "Dear Evan Hansen official soundtrack"
video_url = search_youtube(search_query)

# 결과 출력
print(f"🎵 검색된 비디오: {video_url}")
