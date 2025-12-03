import os
import csv
import datetime

import streamlit as st
from openai import OpenAI

# -----------------------------
# 기본 설정
# -----------------------------
MAX_TURNS = 5        # 턴 수
MAX_LIKING = 100     # 최대 호감도

# 현재 app 파일 위치 (이미지/점수 파일 경로용)
BASE_DIR = os.path.dirname(__file__)
SCORE_FILE = os.path.join(BASE_DIR, "scores.csv")

# OpenAI 클라이언트 초기화
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
    st.session_state.nickname = ""
    st.session_state.score_saved = False
    st.session_state.speech_style = "더 자연스럽게"


def get_expression_image(liking: int, gender: str, mbti: str) -> str:
    """
    호감도/성별/MBTI 기준으로 보여줄 표정 이미지 경로 반환
    - 파일명 규칙: happy_male_F.png / sad_female_T.png 같은 형태
    """
    feeling = "happy" if liking >= 70 else "neutral" if liking >= 40 else "sad"
    gender_key = "male" if gender == "남성" else "female"
    ft_key = "F" if "F" in mbti else "T"
    return os.path.join(BASE_DIR, "images", f"{feeling}_{gender_key}_{ft_key}.png")


def get_style_instruction(style: str) -> str:
    """말투 옵션에 따라 스타일 설명 문장 생성"""
    if style == "더 세게":
        return (
            "전체적으로 도도하고 약간 직설적인 말투를 사용하라. "
            "감정을 크게 드러내지 않으며 쿨한 느낌을 유지한다."
        )
    elif style == "더 수줍게":
        return (
            "말투는 조심스럽고 부끄러움을 타며, 문장 끝에 망설임이 느껴지는 표현을 사용한다. "
            "감정 표현은 작고 여린 편이다."
        )
    elif style == "더 활발하게":
        return (
            "말투는 밝고 텐션이 높으며, 리액션이 크고 감정 표현이 적극적이다. "
            "친근하고 에너지 넘치는 분위기로 말한다."
        )
    # 기본: 더 자연스럽게
    return (
        "말투는 자연스럽고 캐주얼하며, 일상 대화처럼 편안하고 부드럽다."
    )


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
        cause = getattr(e, "__cause__", None)
        if cause is not None:
            st.code(f"원인: {type(cause).__name__} - {cause}")
        st.info("네트워크 또는 API 키 설정을 다시 확인해주세요.")
        return None


def save_score():
    """게임이 끝났을 때 점수를 scores.csv에 기록"""
    if st.session_state.score_saved:
        return  # 중복 저장 방지

    os.makedirs(BASE_DIR, exist_ok=True)
    file_exists = os.path.exists(SCORE_FILE)

    with open(SCORE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # 처음 만들 때 헤더 작성
        if not file_exists:
            writer.writerow(
                ["nickname", "mbti", "gender", "age", "liking", "ending", "timestamp"]
            )

        writer.writerow(
            [
                st.session_state.nickname,
                st.session_state.partner_mbti,
                st.session_state.partner_gender,
                st.session_state.partner_age,
                st.session_state.liking,
                st.session_state.ending_message,
                datetime.datetime.now().isoformat(timespec="seconds"),
            ]
        )

    st.session_state.score_saved = True


def load_scores():
    """저장된 점수 읽어오기 (리스트[dict])"""
    if not os.path.exists(SCORE_FILE):
        return []

    scores = []
    with open(SCORE_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["liking"] = int(row["liking"])
            except Exception:
                row["liking"] = 0
            scores.append(row)
    return scores


# -----------------------------
# 세션 상태 초기화
# -----------------------------
if "history" not in st.session_state:
    reset_game()


# -----------------------------
# UI 시작
# -----------------------------
st.title("💔 MBTI 소개팅 Q&A 게임")

# 1. 닉네임 / MBTI / 성별 / 나이대 / 말투 선택 단계
if not st.session_state.game_started:
    st.session_state.nickname = st.text_input(
        "당신의 닉네임을 입력하세요:",
        value=st.session_state.get("nickname", ""),
        max_chars=20,
        placeholder="예: zoe",
    )

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

    st.session_state.speech_style = st.selectbox(
        "상대방의 말투 스타일을 골라주세요:",
        ["더 자연스럽게", "더 세게", "더 수줍게", "더 활발하게"],
    )

    if st.button("💕 소개팅 시작"):
        if not st.session_state.nickname.strip():
            st.warning("닉네임을 먼저 입력해주세요!")
        else:
            style_instruction = get_style_instruction(st.session_state.speech_style)

            # 시스템 프롬프트 세팅
            system_prompt = (
                f"너는 소개팅에 나온 상대방이다. "
                f"MBTI는 '{st.session_state.partner_mbti}'이고, "
                f"성별은 '{st.session_state.partner_gender}', "
                f"나이대는 '{st.session_state.partner_age}'이다. "
                "MBTI, 성별, 나이대에 맞는 말투와 성격을 반영해서 대답하라. "
                f"{style_instruction} "
                "첫 턴에서는 자연스럽고 편안하게 인사하고 대화를 자연스럽게 시작하라. "
                "질문을 꼭 하지 않아도 된다."
            )

            st.session_state.history = [{"role": "system", "content": system_prompt}]
            st.session_state.turn = 1
            st.session_state.game_started = True
            st.session_state.liking = 50
            st.session_state.ending_message = None
            st.session_state.score_saved = False

            # 첫 질문(또는 첫 멘트) 생성
            question = call_chat(
                st.session_state.history,
                temperature=0.7,
                max_tokens=100,
            )
            if question is not None:
                st.session_state.history.append(
                    {"role": "assistant", "content": question}
                )
                st.rerun()


# 2. 게임 진행 단계
if st.session_state.game_started:
    st.write(f"플레이어: **{st.session_state.nickname}**")
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
            st.markdown(f"**{st.session_state.nickname}:** {msg['content']}")

    # 플레이어 답변 입력
    if st.session_state.turn <= MAX_TURNS and not st.session_state.ending_message:
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
                response_prompt = st.session_state.history.copy()
                style_instruction = get_style_instruction(
                    st.session_state.speech_style
                )

                # 이후 턴에 적용할 system 프롬프트
                response_prompt.insert(
                    0,
                    {
                        "role": "system",
                        "content": (
                            f"너는 소개팅에 나온 상대방이다. "
                            f"MBTI는 '{st.session_state.partner_mbti}'이고, "
                            f"성별은 '{st.session_state.partner_gender}', "
                            f"나이대는 '{st.session_state.partner_age}'이다. "
                            f"{style_instruction} "
                            "플레이어의 말에 자연스럽게 공감하거나 반응하며 편안하게 대화를 이어가라. "
                            "질문을 반드시 할 필요는 없으며, 친구처럼 자연스럽게 대화하라."
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

                # 점수 저장
                save_score()

            st.rerun()

    # 엔딩 + 다시 시작 버튼
    if st.session_state.ending_message:
        st.markdown("---")
        st.markdown(f"**엔딩:** {st.session_state.ending_message}")
        st.markdown(f"최종 호감도: **{st.session_state.liking} / {MAX_LIKING}**")

        if st.button("🔄 다시 도전하기"):
            reset_game()
            st.rerun()

# -----------------------------
# 랭킹 표시
# -----------------------------
st.markdown("---")
st.subheader("🏆 최근 플레이어 랭킹 (호감도 순 Top 10)")

scores = load_scores()
if scores:
    # 호감도 높은 순 정렬
    scores_sorted = sorted(scores, key=lambda x: x["liking"], reverse=True)[:10]

    # 순위(1부터 시작) 컬럼 추가
    ranked_scores = []
    for i, s in enumerate(scores_sorted, start=1):
        ranked_scores.append(
            {
                "순위": i,
                "닉네임": s["nickname"],
                "MBTI": s["mbti"],
                "성별": s["gender"],
                "나이대": s["age"],
                "호감도": s["liking"],
                "엔딩": s["ending"],
            }
        )

    st.table(ranked_scores)

else:
    st.write("아직 기록된 점수가 없습니다. 첫 번째로 도전해보세요!")
