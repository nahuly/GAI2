import streamlit as st
from main import data


def show_results():
    st.title("당신의 최애 정령 순위")

    if st.session_state.results:
        for rank, (spirit, score) in enumerate(st.session_state.results[:3], 1):
            st.subheader(f"{rank}위: {spirit}")
            st.write(f"소속: {data.loc['소속', spirit]}")
            st.write(f"특기: {data.loc['특기', spirit]}")
            st.write(f"취미: {data.loc['취미', spirit]}")
            st.write("---")
    else:
        st.write("아직 결과가 없습니다. 메인 페이지에서 질문에 답해주세요.")


if __name__ == "__main__":
    show_results()
