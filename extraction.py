# Import python packages
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import plotly.express as px


session = get_active_session()


# Write directly to the app
st.title("추출 :balloon:")


st.header("추출 개수")
st.metric(label='총 추출 개수', value='222')
st.metric(label='총 추출 개수', value='222', delta='-50%')


df = pd.DataFrame(
    {
        "a": range(1, 3),  # 리스트로 값 전달
        "b": range(1, 3),  # 리스트로 값 전달
    }
)


# 데이터프레임을 bar_chart로 시각화
# st.bar_chart(df, x = "a", y = "b")


session = get_active_session()

st.header("sql 숫자 데이터")
st.text(220)

# -----------------------------------------------------------

st.header("sql 그래프")

df = pd.DataFrame(
    {
        "a": [1],  # 리스트로 값 전달
        "b": [2],  # 리스트로 값 전달
    }
)

# 데이터프레임을 bar_chart로 시각화
st.bar_chart(df)
