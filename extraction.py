import streamlit as st
import pandas as pd
import sqlite3  # 예시로 SQLite 사용

# 데이터베이스 연결 (SQLite 예제)


@st.cache_resource
def get_connection():
    conn = sqlite3.connect("game_data.db")  # 데이터베이스 파일 경로
    return conn

# 쿼리 실행 함수


def execute_query(query, params=()):
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"쿼리 실행 중 오류 발생: {e}")
        return pd.DataFrame()


# Streamlit 인터페이스
st.title("게임 유저 분석 도구")

# 사용자 질문 입력
user_question = st.text_input(
    "질문을 입력하세요:", "2024-10-23에 접속한 유저 중 100만원 이상 쓴 유저는?")

# 질문에 따른 쿼리 처리
if st.button("분석 실행"):
    if "2024-10-23에 접속한 유저 중 100만원 이상 쓴 유저는" in user_question:
        # 해당 질문에 대응하는 SQL 쿼리
        query = """
        SELECT A.id
        FROM 테이블A A
        JOIN 테이블B B
          ON A.id = B.id
        WHERE A.일_별_날짜 = ?
        GROUP BY A.id
        HAVING SUM(B.구매_가격) >= 1000000;
        """
        date = "2024-10-23"  # 질문에서 추출된 날짜
        result = execute_query(query, params=(date,))

        if not result.empty:
            st.success("분석 결과:")
            st.dataframe(result)
        else:
            st.info("조건에 맞는 유저가 없습니다.")
    else:
        st.warning("해당 질문은 현재 지원하지 않습니다.")

# 참고: 데이터베이스 스키마 예시
# 테이블A: (일_별_날짜 TEXT, id INTEGER, 레벨 INTEGER, 마지막_접속날짜 TEXT, 서버 TEXT, 오늘_접속여부 INTEGER, 날짜_차이 INTEGER)
# 테이블B: (일_별_날짜 TEXT, id INTEGER, 구매_아이템 TEXT, 구매_가격 INTEGER)
