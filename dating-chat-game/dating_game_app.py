import os
import streamlit as st
from openai import OpenAI

# -----------------------------
# 기본 설정
# -----------------------------
MAX_TURNS = 5        # 턴 수
MAX_LIKING = 100     # 최대 호감도

# 현재 app 파일 위치 (이미지 경로용)
BASE_DIR = os.path.dirname(__file__)

# OpenAI 클라이언트 초기화
# st.secrets에 OPENAI_API_KEY가 들어있다고 가정
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# -----------------------------
# 유틸 함수들
# -----------------------------
def reset_game():
    """게임용 세션 상태 초기화"""
    st.session_state.history = []
    st.session_state.liking = 50
    st.session_state.turn = 0
    st.session_state.game_started = False
    st.session_state.ending_message = None
    st.session_state.partner_mbti = None
    st.session_state.partner_gender = None
    st.session_state.partner_age = None


def get_expression_image(liking: int, gender: str, mbti: str) -> str:
    """
    호감도/성별/MBTI 기준으로 보여줄 표정 이미지 경로 반환
    - 파일명 규칙: happy_male_F.png / sad_female_T.png 같은 형태
    """
    feeling = "happy" if liking >= 70 else "neutral" if liking >= 40 else "sad"
    gender_key = "male" if gender == "남성" else "female"
    ft_key = "F" if "F" in mbti else "T"
    return os.path.join(BASE_DIR, "images", f"{feeling}_{gender_key}_{ft_key}.png")


def call_chat(messages, model="gpt-4.1", **kwargs):
    """
    OpenAI Chat 호출 래퍼. 에러가 나면 스트림릿에 표시하고 None 리턴.
    """
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs,
        )
        return resp.choices[0].message.content
    except Exception as e:
        st.error(f"❌ OpenAI 호출 중 오류가 발생했습니다: {type(e).__name__}")
        st.info("네트워크 또는 API 키 설정을 다시 확인해주세요.")
        return None


# -----------------------------
# 세션 상태 초기화
# -----------------------------
if "history" not in st.session_state:
    reset_game()


# -----------------------------
# UI 시작
# -----------------------------
st.title("💔 MBTI 소개팅 Q&A 게임")

# 디버그용: 키 존재 여부만 확인 (원하면 주석 해제)
# st.write("🔑 OPENAI_API_KEY 존재 여부:", "OPENAI_API_KEY" in st.secrets)

# 1. MBTI / 성별 / 나이대 선택 단계
if not st.session_state.game_started:
    st.session_state.partner_mbti = st.selectbox(
        "상대방의 MBTI를 골라주세요:",
        [
            "INTJ", "INTP", "ENTJ", "ENTP",
            "INFJ", "INFP", "ENFJ", "ENFP",
            "ISTJ", "ISFJ", "ESTJ", "ESFJ",
            "ISTP", "ISFP", "ESTP", "ESFP",
        ],
    )

    st.session_state.partner_gender = st.radio(
        "상대방의 성별을 선택하세요:",
        ["남성", "여성"],
    )

    st.session_state.partner_age = st.selectbox(
        "상대방의 나이대를 선택하세요:",
        ["10대", "20대", "30대", "40대", "50대 이상"],
    )

    if st.button("💕 소개팅 시작"):
        # 시스템 프롬프트 세팅
        system_prompt = (
            f"너는 소개팅에 나온 상대방이다. "
            f"MBTI는 '{st.session_state.partner_mbti}'이고, "
            f"성별은 '{st.session_state.partner_gender}', "
            f"나이대는 '{st.session_state.partner_age}'이다. "
            "MBTI, 성별, 나이대에 맞는 말투와 성격을 반영해서 대답하라. "
            "첫 턴에서는 반드시 플레이어에게 짧고 자연스러운 질문을 한 가지 던져라. "
            "불필요한 긴 설명은 하지 말고 반드시 질문으로 끝내라."
        )

        st.session_state.history = [{"role": "system", "content": system_prompt}]
        st.session_state.turn = 1
        st.session_state.game_started = True
        st.session_state.liking = 50

        # 첫 질문 생성
        question = call_chat(
            st.session_state.history,
            temperature=0.7,
            max_tokens=100,
        )
        if question is not None:
            st.session_state.history.append({"role": "assistant", "content": question})
            st.rerun()


# 2. 게임 진행 단계
if st.session_state.game_started:
    st.write(f"턴: {st.session_state.turn}/{MAX_TURNS}")
    st.progress(
        st.session_state.liking / MAX_LIKING,
        text=f"💖 호감도: {st.session_state.liking}/{MAX_LIKING}",
    )

    # 표정 이미지 표시
    expression_img = get_expression_image(
        st.session_state.liking,
        st.session_state.partner_gender,
        st.session_state.partner_mbti,
    )
    if os.path.exists(expression_img):
        st.image(expression_img, width=350, caption="상대방의 표정")
    else:
        st.write("⚠️ 맞는 이미지가 없습니다. 이미지 파일명을 확인하세요.")

    # 대화 기록 표시
    for msg in st.session_state.history:
        if msg["role"] == "assistant":
            st.markdown(
                f"**상대방 ({st.session_state.partner_mbti}, "
                f"{st.session_state.partner_gender}, "
                f"{st.session_state.partner_age}):** {msg['content']}"
            )
        elif msg["role"] == "user":
            st.markdown(f"**플레이어:** {msg['content']}")

    # 플레이어 답변 입력
    if st.session_state.turn <= MAX_TURNS and not st.session_state.ending_message:
        # 턴마다 key 달리해서 입력창 유지
        player_answer = st.text_input(
            "👉 당신의 대답:",
            key=f"turn_{st.session_state.turn}",
        )

        if st.button("전송", key=f"send_{st.session_state.turn}"):
            if not player_answer.strip():
                st.warning("먼저 대답을 입력해주세요!")
                st.stop()

            # 플레이어 메시지 추가
            st.session_state.history.append(
                {"role": "user", "content": player_answer}
            )

            # ---- 1) 호감도 판정 ----
            judge_prompt = [
                {
                    "role": "system",
                    "content": (
                        f"너는 까다로운 소개팅 판정관이다. "
                        f"상대방의 MBTI는 '{st.session_state.partner_mbti}'이고, "
                        f"성별은 '{st.session_state.partner_gender}', "
                        f"나이대는 '{st.session_state.partner_age}'이다. "
                        "플레이어의 대답을 보고 호감도를 평가하라. "
                        "- 성격/성별/나이대와 잘 맞고 매력적이면 '+15'. "
                        "- 그 외의 모든 경우는 무조건 '-15'. "
                        "반드시 +15 또는 -15 중 하나만 출력하라."
                    ),
                },
                {
                    "role": "user",
                    "content": f"플레이어: {player_answer}",
                },
            ]

            judge_result = call_chat(
                judge_prompt,
                max_tokens=10,
            )

            if judge_result is None:
                # 판정이 실패하면 더 진행하지 않고 중단
                st.stop()

            judge_result = judge_result.strip()
            if "+15" in judge_result:
                st.session_state.liking = min(
                    MAX_LIKING, st.session_state.liking + 15
                )
            else:
                st.session_state.liking = max(0, st.session_state.liking - 15)

            # 턴 증가
            st.session_state.turn += 1

            # ---- 2) 다음 상대방 대답 or 엔딩 ----
            if st.session_state.turn <= MAX_TURNS:
                # 이전 대화 히스토리를 그대로 사용하되,
                # 두 번째 턴 이후에는 새로운 system 프롬프트를 맨 앞에 추가
                response_prompt = st.session_state.history.copy()

                if st.session_state.turn > 1:
                    response_prompt.insert(
                        0,
                        {
                            "role": "system",
                            "content": (
                                f"너는 소개팅에 나온 상대방이다. "
                                f"MBTI는 '{st.session_state.partner_mbti}'이고, "
                                f"성별은 '{st.session_state.partner_gender}', "
                                f"나이대는 '{st.session_state.partner_age}'이다. "
                                "플레이어의 대답에 공감하거나 반응하면서 "
                                "MBTI/성별/나이대 특성을 반영한 자연스러운 대답을 하라. "
                                "꼭 질문으로 끝낼 필요는 없지만, "
                                "자연스럽게 이어질 수 있도록 가끔은 질문을 포함해도 된다."
                            ),
                        },
                    )

                answer = call_chat(
                    response_prompt,
                    temperature=0.8,
                    max_tokens=150,
                )
                if answer is not None:
                    st.session_state.history.append(
                        {"role": "assistant", "content": answer}
                    )
            else:
                # 엔딩 결정
                if st.session_state.liking >= 70:
                    st.session_state.ending_message = (
                        "🎉 소개팅 대성공! 서로 연락을 이어가기로 했습니다 💕"
                    )
                elif st.session_state.liking >= 40:
                    st.session_state.ending_message = (
                        "🙂 분위기는 무난했지만 큰 진전은 없었습니다."
                    )
                else:
                    st.session_state.ending_message = (
                        "💔 상대방이 실망했습니다. 소개팅 실패..."
                    )

            st.rerun()

    # 엔딩 + 다시 시작 버튼
    if st.session_state.ending_message:
        st.markdown("---")
        st.markdown(st.session_state.ending_message)
        if st.button("🔄 다시 도전하기"):
            reset_game()
            st.rerun()
