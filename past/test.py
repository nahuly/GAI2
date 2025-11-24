import streamlit as st
import requests
import pandas as pd
from xml.etree import ElementTree as ET

st.title('뮤지컬 공연 정보')

# URL 입력 (여기에 올바른 API 키를 넣어주세요)
url = "http://www.kopis.or.kr/openApi/restful/pblprfr?service=API_KEY&stdate=20240101&eddate=20241001&cpage=1&rows=1000&shcate=GGGA&signgucode=11"

# URL 불러오기
response = requests.get(url)

# 성공적으로 데이터를 가져왔는지 확인
if response.status_code == 200:
    # XML 파싱
    root = ET.fromstring(response.content)

    # 데이터 추출
    data = []
    for item in root.findall('.//db'):
        row = {}
        for child in item:
            row[child.tag] = child.text
        data.append(row)

    # DataFrame 생성
    df = pd.DataFrame(data)

    # 열 이름 변경
    df1 = df.rename(columns={'prfnm': 'name', 'prfpdfrom': 'strt_ymd', 'prfpdfrom': 'strt_ymd',
                    'prfpdto': 'end_ymd', 'fcltynm': 'place', 'prfstate': 'state'})

    # DataFrame 출력
    st.write(df)
else:
    st.error("데이터를 불러오지 못했습니다. API 키를 확인해주세요.")
