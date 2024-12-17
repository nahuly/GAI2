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
st.bar_chart(id_stats['cnt'])
# -----------------------------------------------------------

df_group = pd.read_csv('test_group.csv')
merged_df = pd.merge(id_stats, df_group, on='AgitID', how='left')

# 결과 확인
st.bar_chart(merged_df.set_index('cell')['cnt'])

# -----------------------------------------------------------
# group별로 cnt 값 합산
grouped_stats = merged_df.groupby('cell')['cnt'].sum().reset_index()
# 원차트로 시각화
fig = px.pie(grouped_stats, names='cell',
             values='cnt', title='Group-wise Count')

# Streamlit에서 그래프 표시
st.plotly_chart(fig)


# -----------------------------------------------------------

# 'Date' 컬럼에서 월만 추출
df['Month'] = df['Date'].str[5:7]

# 'Month'별로 'cnt' 합산
month_stats = df.groupby('Month').agg(
    cnt=('Month', 'size'),  # 행의 개수
)

# 결과를 Streamlit의 bar_chart로 시각화
st.bar_chart(month_stats.set_index('Month')['cnt'])
