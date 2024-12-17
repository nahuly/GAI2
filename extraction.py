# Import python packages
import streamlit as st
import pandas as pd
import plotly.express as px


# Write directly to the app
st.title("추출 :balloon:")

cnt = pd.read_csv('test.csv')


st.header("추출 개수")
st.metric(label='총 추출 개수', value=len(cnt))
st.metric(label='총 추출 개수', value=len(cnt), delta='-50%')

# -----------------------------------------------------------
df = pd.DataFrame(
    {
        "a": range(1, 3),  # 리스트로 값 전달
        "b": range(1, 3),  # 리스트로 값 전달
    }
)

st.header("sql 그래프")

df = pd.DataFrame(
    {
        "a": range(1, 3),  # 리스트로 값 전달
        "b": range(2, 4),  # 리스트로 값 전달
    }
)

# 데이터프레임을 bar_chart로 시각화
st.bar_chart(df, x="a", y="b")
