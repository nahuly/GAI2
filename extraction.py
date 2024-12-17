# Import python packages
import streamlit as st
import pandas as pd
import plotly.express as px


# Write directly to the app
st.title("추출 :balloon:")

df = pd.read_csv('test.csv')


st.header("추출 개수")
st.metric(label='총 추출 개수', value=len(df))
st.metric(label='총 추출 개수', value=len(df), delta='-50%')

# -----------------------------------------------------------

id_stats = df.groupby('AgitID').agg(
    cnt=('AgitID', 'size'),  # 행의 개수
)

# 데이터프레임을 bar_chart로 시각화
st.bar_chart(df, x="AgitID", y="cnt")
