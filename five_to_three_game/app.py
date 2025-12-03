import random
import time
import streamlit as st

st.set_page_config(page_title="5명 중 3명 뽑기", page_icon="🎲")

st.title("🎲 5명 중 3명 랜덤 뽑기 게임 (긴장감 MAX 룰렛)")

st.write("이름 5명을 입력하고 버튼을 눌러 **천천히, 긴장되게 3명을 뽑아보세요!**")

# 이름 입력 받기
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    name1 = st.text_input("1번", "A")
with col2:
    name2 = st.text_input("2번", "B")
with col3:
    name3 = st.text_input("3번", "C")
with col4:
    name4 = st.text_input("4번", "D")
with col5:
    name5 = st.text_input("5번", "E")

names = [name1, name2, name3, name4, name5]

st.divider()

# 연출 길이 조절 (긴장감 슬라이더)
drama_level = st.slider("연출 강도 (길이)", 1, 5, 3, help="숫자가 클수록 더 오래, 더 천천히 뽑혀요!")

# 뽑기 버튼
if st.button("🎰 긴장감 있게 룰렛 돌리기!"):
    # 공백 이름 제거
    valid_names = [n for n in names if n.strip() != ""]

    if len(valid_names) < 3:
        st.error("최소 3명 이상 입력해야 뽑을 수 있어요!")
    elif len(valid_names) > 5:
        st.error("최대 5명까지만 사용 가능합니다.")
    else:
        st.info("참가자 확정! 곧 룰렛이 시작됩니다...")

        # 🔢 카운트다운 연출
        countdown_placeholder = st.empty()
        for i in range(3, 0, -1):
            countdown_placeholder.markdown(
                f"<h1 style='text-align:center; font-size:60px;'>⏳ {i}</h1>",
                unsafe_allow_html=True
            )
            time.sleep(0.8)
        countdown_placeholder.markdown(
            "<h1 style='text-align:center; font-size:60px;'>🎰 START!</h1>",
            unsafe_allow_html=True
        )
        time.sleep(0.7)
        countdown_placeholder.empty()

        # 룰렛 애니메이션용
        placeholder = st.empty()
        progress_bar = st.progress(0)

        # 연출 길이에 따라 회전 횟수/속도 조정
        fast_spins = 25 * drama_level      # 빠르게 돌아가는 횟수
        slow_spins = 12 * drama_level      # 느려지며 돌아가는 횟수

        total_spins = fast_spins + slow_spins

        # 1단계: 빠르게 섞이기
        for i in range(fast_spins):
            temp_pick = random.sample(valid_names, min(3, len(valid_names)))
            placeholder.markdown(
                f"🔄 **섞는 중...** `{', '.join(temp_pick)}`"
            )
            progress_bar.progress(int((i + 1) / total_spins * 100))
            time.sleep(0.04)  # 빠른 구간

        # 2단계: 점점 느려지며 섞이기 (긴장 구간)
        for i in range(slow_spins):
            temp_pick = random.sample(valid_names, min(3, len(valid_names)))
            placeholder.markdown(
                f"😵‍💫 아직 몰라요... **{', '.join(temp_pick)}**"
            )
            progress_bar.progress(int((fast_spins + i + 1) / total_spins * 100))
            time.sleep(0.11 + 0.02 * drama_level)  # 느려지는 느낌

        # 최종 당첨자
        winners = random.sample(valid_names, 3)

        placeholder.empty()
        progress_bar.empty()

        st.markdown("## 🎉 최종 당첨자, 한 명씩 공개합니다...")

        medal_emojis = ["🥇", "🥈", "🥉"]
        # 3등 → 2등 → 1등 순으로 공개해서 더 긴장되게
        reveal_order = [2, 1, 0]  # 인덱스 (3등, 2등, 1등)

        for idx in reveal_order:
            slot = st.empty()
            medal = medal_emojis[idx]
            rank = idx + 1

            # 1) ??? 연출
            slot.markdown(
                f"### {medal} {rank}등은... **???**",
            )
            time.sleep(1.3 + 0.3 * drama_level)

            # 2) 진짜 이름 공개
            slot.markdown(
                f"### {medal} {rank}등: **{winners[idx]}** 🎉"
            )
            time.sleep(1.0 + 0.2 * drama_level)

        st.balloons()

st.caption("Made with Streamlit ✨ 긴장되는 추첨용으로 쓰기 딱 좋음")
