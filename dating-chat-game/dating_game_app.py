import os
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

MAX_TURNS = 3
MAX_LIKING = 100

# 세션 초기화 함수
def reset_game():
    st.session_state.history = []
    st.session_state.liking = 50
    st.session_state.turn = 0
    st.session_state.game_started = False
    st.session_state.ending_message = None
    st.session_state.partner_personality = None

# 세션 상태 초기화
if "history" not in st.session_state:
    reset_game()

st.title("💔 까다로운 소개팅 Q&A 게임")

# 1. 성격 선택
if not st.session_state.game_started:
    st.session_state.partner_personality = st.selectbox(
        "상대방의 성격을 골라주세요:",
        ["밝고 활발한", "차분하고 지적인", "장난꾸러기 같은", "새침하고 도도한"]
    )
    if st.button("💕 소개팅 시작"):
        st.session_state.history = [
            {"role": "system", "content": (
                f"너는 소개팅에 나온 상대방이다. "
                f"성격은 '{st.session_state.partner_personality}' 스타일이다. "
                "매 턴마다 플레이어에게 짧고 자연스러운 질문을 한 가지 던져라. "
                "불필요한 긴 설명은 하지 말고, 반드시 질문으로 끝내라."
            )}
        ]
        st.session_state.turn = 1
        st.session_state.game_started = True
        st.session_state.liking = 50

        # 첫 질문 생성
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state.history,
            temperature=0.7,
            max_tokens=100
        )
        question = response.choices[0].message.content
        st.session_state.history.append({"role": "assistant", "content": question})
        st.rerun()

# 2. 진행 단계
if st.session_state.game_started:
    st.write(f"턴: {st.session_state.turn}/{MAX_TURNS}")
    st.progress(st.session_state.liking / MAX_LIKING,
                text=f"💖 호감도: {st.session_state.liking}/{MAX_LIKING}")

    # 대화 표시
    for msg in st.session_state.history:
        if msg["role"] == "assistant":
            st.markdown(f"**상대방:** {msg['content']}")
        elif msg["role"] == "user":
            st.markdown(f"**플레이어:** {msg['content']}")

    # 답변 입력
    if st.session_state.turn <= MAX_TURNS and not st.session_state.ending_message:
        player_answer = st.text_input("👉 당신의 대답:", key=f"turn_{st.session_state.turn}")
        if st.button("전송", key=f"send_{st.session_state.turn}"):
            st.session_state.history.append({"role": "user", "content": player_answer})

            # 호감도 판정
            judge_prompt = [
                {"role": "system", "content": (
                    f"너는 까다로운 소개팅 판정관이다. "
                    f"상대방의 성격은 '{st.session_state.partner_personality}'이다. "
                    "플레이어의 대답을 보고 호감도를 평가하라. "
                    "- 성격에 잘 맞고 매력적이면 '+15'. "
                    "- 그 외의 모든 경우는 무조건 '-15'. "
                    "반드시 +15 또는 -15 중 하나만 출력하라."
                )},
                {"role": "user", "content": f"플레이어: {player_answer}"}
            ]

            judge = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=judge_prompt,
                max_tokens=10
            ).choices[0].message.content.strip()

            if "+15" in judge:
                st.session_state.liking = min(MAX_LIKING, st.session_state.liking + 15)
            else:  # 무조건 -15
                st.session_state.liking = max(0, st.session_state.liking - 15)

            # 턴 증가
            st.session_state.turn += 1

            # 다음 질문 or 엔딩
            if st.session_state.turn <= MAX_TURNS:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.history,
                    temperature=0.7,
                    max_tokens=100
                )
                question = response.choices[0].message.content
                st.session_state.history.append({"role": "assistant", "content": question})
            else:
                if st.session_state.liking >= 70:
                    st.session_state.ending_message = "🎉 소개팅 대성공! 서로 연락을 이어가기로 했습니다 💕"
                elif st.session_state.liking >= 40:
                    st.session_state.ending_message = "🙂 분위기는 무난했지만 큰 진전은 없었습니다."
                else:
                    st.session_state.ending_message = "💔 상대방이 실망했습니다. 소개팅 실패..."

            st.rerun()

    # 엔딩 메시지 + 다시 도전
    if st.session_state.ending_message:
        st.markdown(st.session_state.ending_message)
        if st.button("🔄 다시 도전하기"):
            reset_game()
            st.rerun()
