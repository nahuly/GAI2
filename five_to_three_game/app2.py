import random
import time
import streamlit as st

st.set_page_config(page_title="폭탄 전달 생존 게임", page_icon="💣")

st.title("💣 폭탄 전달 랜덤 생존 게임")

st.write(
    """
    5명의 이름을 입력하고 **폭탄 전달 게임**을 시작해보세요!  
    폭탄이 이리저리 돌아다니다가 💥 터지면,  
    그 사람은 탈락... 😱  
    두 번의 폭발 후 **살아남은 3명이 최종 생존자 / 당첨자**입니다.
    """
)

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

# 연출 강도 (길게/짧게 조절)
drama_level = st.slider(
    "연출 강도 (길이 / 긴장감)", 1, 5, 3,
    help="숫자가 클수록 폭탄이 더 오래 돌아다녀요!"
)

def render_board(alive, holder, round_idx=None, pass_idx=None):
    """이름 줄 + 폭탄 위치 줄을 예쁘게 보여주는 함수"""
    name_row = " | ".join([f"**{n}**" for n in alive])
    bomb_row = " | ".join(["💣" if n == holder else "⬜️" for n in alive])

    subtitle = ""
    if round_idx is not None and pass_idx is not None:
        subtitle = f"<p style='text-align:center; font-size:14px;'>라운드 {round_idx} · 패스 {pass_idx}</p>"

    html = f"""
    <div style="text-align:center; font-size:20px; margin-top:10px;">
        <p>{name_row}</p>
        <p>{bomb_row}</p>
        {subtitle}
    </div>
    """
    return html

if st.button("💣 폭탄 게임 시작하기!"):
    # 공백 제거
    valid_names = [n for n in names if n.strip() != ""]

    if len(valid_names) < 3:
        st.error("최소 3명 이상 입력해야 게임을 시작할 수 있어요!")
    elif len(valid_names) > 5:
        st.error("최대 5명까지만 사용 가능합니다.")
    else:
        st.success("참가자 확정! 폭탄 게임을 시작합니다 🔥")

        st.write("👥 참가자:")
        st.write(", ".join(f"**{n}**" for n in valid_names))

        # 폭탄 연출 파라미터
        min_passes = 6 * drama_level
        max_passes = 12 * drama_level

        alive = valid_names.copy()
        losers = []

        # 5명 중 2명 탈락 → 3명 생존
        num_bombs = len(valid_names) - 3

        for bomb_round in range(1, num_bombs + 1):
            st.subheader(f"💣 폭탄 라운드 {bomb_round}")

            board_placeholder = st.empty()
            text_placeholder = st.empty()
            progress_bar = st.progress(0)

            # 라운드 시작 시 폭탄을 누가 먼저 들고 있을지 랜덤
            current_holder = random.choice(alive)

            # 몇 번 전달될지 랜덤
            passes = random.randint(min_passes, max_passes)

            for i in range(passes):
                # 현재 보드 상태 표시 (폭탄 위치 포함)
                board_html = render_board(alive, current_holder, bomb_round, i + 1)
                board_placeholder.markdown(board_html, unsafe_allow_html=True)

                # 다음 사람은 현재 사람 빼고 랜덤
                next_holder = random.choice([p for p in alive if p != current_holder])

                text_placeholder.markdown(
                    f"👉 폭탄 전달 중... **{current_holder} → {next_holder}**"
                )

                current_holder = next_holder

                progress_bar.progress(int((i + 1) / passes * 100))
                time.sleep(0.10 + 0.02 * drama_level)  # 여기서 긴장감 조절

            # 마지막 상태 한 번 더 렌더링
            board_html = render_board(alive, current_holder, bomb_round, passes)
            board_placeholder.markdown(board_html, unsafe_allow_html=True)

            # 폭발 연출
            time.sleep(0.5)
            text_placeholder.markdown(
                f"💥 폭탄 폭발!! **{current_holder}** 탈락... 😱"
            )
            losers.append(current_holder)
            alive = [p for p in alive if p != current_holder]

            progress_bar.empty()
            time.sleep(1.2)

            st.write("✅ 현재 생존자:", ", ".join(f"**{n}**" for n in alive))
            st.write("---")

        # 최종 생존자 = 당첨자
        winners = alive.copy()
        random.shuffle(winners)

        st.markdown("## 🏆 최종 생존자 / 당첨자 3명")

        medal_emojis = ["🥇", "🥈", "🥉"]
        for i, w in enumerate(winners):
            st.markdown(f"{medal_emojis[i]} **{i+1}등: {w}** 🎉")
            time.sleep(0.5)

        if losers:
            st.markdown("### 💀 탈락자")
            st.write(", ".join(f"**{n}**" for n in losers))

        st.balloons()

st.caption("Made with Streamlit · 폭탄 돌리기 (위치 시각화 버전) 💣")
