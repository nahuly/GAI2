import os
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------
# 0. 기본 세팅
# ---------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.warning("⚠️ OPENAI_API_KEY가 설정되어 있지 않습니다. .env 또는 환경변수를 확인해 주세요.")
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(
    page_title="친해지길 바래 – CSV 기반 팀 퀴즈",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 친해지길 바래 – CSV 기반 팀 퀴즈")
st.caption("CSV에 있는 우리 팀 데이터를 가지고 OpenAI가 자동으로 퀴즈를 만들어줍니다.")

# ---------------------------
# 1. CSV 업로드
# ---------------------------
uploaded_file = st.file_uploader("팀 정보 CSV 파일을 업로드하세요", type=["csv"])

default_num_questions = 10
num_questions = st.sidebar.slider("생성할 문제 개수", 5, 30, default_num_questions)

quiz_state = st.session_state

if "questions" not in quiz_state:
    quiz_state.questions = []  # [{question, answer, explanation}, ...]
if "current_idx" not in quiz_state:
    quiz_state.current_idx = 0
if "score" not in quiz_state:
    quiz_state.score = 0
if "time_left" not in quiz_state:
    quiz_state.time_left = 10
if "started" not in quiz_state:
    quiz_state.started = False
if "user_answer" not in quiz_state:
    quiz_state.user_answer = ""
if "timer_key" not in quiz_state:
    quiz_state.timer_key = 0  # rerun용

# ---------------------------
# 2. CSV → 퀴즈 생성 함수
# ---------------------------

def generate_quiz_questions(df: pd.DataFrame, n_questions: int = 10):
    """
    OpenAI를 사용해서 DataFrame 기반 퀴즈 n_questions개 생성.
    """
    # 데이터 샘플 텍스트로 변환 (행 전체를 문자열로)
    sample_rows = df.head(50).to_csv(index=False)

    system_prompt = """
너는 회사 팀빌딩용 퀴즈 마스터야.
주어진 CSV 데이터를 보고 팀원 정보를 이해하고,
사람들이 서로를 더 잘 알 수 있도록 퀴즈를 만들어줘.

규칙:
- 퀴즈는 한국어로 작성한다.
- 각 문제는 "question", "answer", "explanation" 3개 필드를 가진 JSON 리스트로 반환한다.
- JSON 이외의 다른 텍스트는 절대 출력하지 말 것.
- question은 짧고 명확한 문장으로.
- answer는 간단한 텍스트 (이름 또는 숫자 등).
- explanation은 정답의 근거를 1~2문장으로 설명 (어떤 컬럼을 보고 만든 건지).
- 팀원 개인정보를 과하게 드러내지 말고, 이미 CSV에 있는 정보 범위 안에서만 사용.
- 예: 입사년도, 소속, MBTI, 워크샵 성향, 혈액형 등을 조합해서 문제를 만든다.
"""

    user_prompt = f"""
아래는 팀 정보 CSV의 내용이야(최대 50행 샘플).

CSV:
---
{sample_rows}
---

이 데이터를 기반으로 서로를 알아갈 수 있는 객관식이 아닌 **주관식 퀴즈** {n_questions}개를 만들어줘.
이름을 맞히거나 숫자를 맞히는 형태 등 자유롭게 섞어서 만들되,
난이도는 너무 어렵지 않게.

반드시 다음 형식의 JSON만 출력해:
[
  {{"question": "질문1...", "answer": "정답1", "explanation": "이유1"}},
  {{"question": "질문2...", "answer": "정답2", "explanation": "이유2"}}
]
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7
    )

    raw = response.output[0].content[0].text  # text만 꺼냄

    import json
    try:
        data = json.loads(raw)
        questions = []
        for item in data:
            q = item.get("question", "").strip()
            a = item.get("answer", "").strip()
            e = item.get("explanation", "").strip()
            if q and a:
                questions.append(
                    {"question": q, "answer": a, "explanation": e}
                )
        return questions
    except Exception as e:
        st.error(f"JSON 파싱에 실패했습니다: {e}")
        st.text(raw)
        return []

# ---------------------------
# 3. 사이드바: CSV 미리보기
# ---------------------------
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("📄 업로드된 CSV 미리보기 (상위 10행)")
    st.dataframe(df.head(10), use_container_width=True)
else:
    st.info("CSV를 올리면 여기에서 미리 볼 수 있어요.")

st.markdown("---")

# ---------------------------
# 4. 퀴즈 생성 버튼
# ---------------------------
if uploaded_file is not None and st.button("🧠 OpenAI로 퀴즈 생성하기", type="primary"):
    with st.spinner("퀴즈 생성 중..."):
        df = pd.read_csv(uploaded_file)
        quiz_state.questions = generate_quiz_questions(df, num_questions)
        quiz_state.current_idx = 0
        quiz_state.score = 0
        quiz_state.started = False
        quiz_state.user_answer = ""
        quiz_state.time_left = 10
        quiz_state.timer_key += 1

    if quiz_state.questions:
        st.success(f"퀴즈 {len(quiz_state.questions)}문제를 생성했습니다! 아래에서 시작할 수 있어요.")

# ---------------------------
# 5. 퀴즈 진행 UI
# ---------------------------
questions = quiz_state.questions

if questions:
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        st.subheader("🎮 퀴즈 플레이")

    with col2:
        st.metric("현재 문제 번호", f"{quiz_state.current_idx + 1} / {len(questions)}")

    with col3:
        st.metric("점수", f"{quiz_state.score} 점")

    st.write("")

    # 현재 문제
    current_q = questions[quiz_state.current_idx]

    # 타이머 표시
    timer_placeholder = st.empty()
    question_placeholder = st.empty()
    answer_placeholder = st.empty()
    result_placeholder = st.empty()
    button_col = st.columns([1,1,1])

    # 시작 버튼
    if not quiz_state.started:
        if st.button("▶ 퀴즈 시작 / 다음 문제", key=f"start_{quiz_state.timer_key}"):
            quiz_state.started = True
            quiz_state.time_left = 10
            quiz_state.user_answer = ""
            result_placeholder.empty()
            st.experimental_rerun()
    else:
        # 타이머 업데이트 (Streamlit 특성상 약식 구현)
        with timer_placeholder:
            st.markdown(f"⏱ 남은 시간: **{quiz_state.time_left}초**")

        # 질문 출력
        with question_placeholder:
            st.markdown(f"**Q. {current_q['question']}**")

        # 답 입력
        with answer_placeholder:
            quiz_state.user_answer = st.text_input(
                "정답을 입력하세요:",
                value=quiz_state.user_answer,
                key=f"answer_{quiz_state.current_idx}",
            )

        # 버튼들
        with button_col[0]:
            submitted = st.button("✅ 정답 제출")
        with button_col[1]:
            passed = st.button("➡ 패스")
        with button_col[2]:
            giveup = st.button("⏹ 종료")

        # 타이머 감소 (대충 1초씩)
        # 이건 '정답 제출 / 패스 / rerun' 이벤트 때만 줄어드는 간단한 버전
        # 진짜 실시간 카운트다운이 필요하면 streamlit-webrtc 같은걸 붙여야해서 여기선 라이트하게 감.
        if quiz_state.time_left > 0:
            quiz_state.time_left -= 1
        else:
            submitted = True  # 시간초과 = 자동 제출 처리
            quiz_state.user_answer = ""  # 빈 답으로 처리

        time.sleep(1)
        st.experimental_rerun()

        # 정답 처리 로직
        if submitted:
            user = (quiz_state.user_answer or "").strip().lower()
            answer_norm = current_q["answer"].strip().lower()

            # 너무 엄격하지 않게 포함여부로도 체크 (이름/아이디 둘 다 가능하게)
            is_correct = (user == answer_norm) or (user and user in answer_norm) or (answer_norm in user)

            if is_correct:
                quiz_state.score += 1
                result_placeholder.success(f"✅ 정답! 정답: {current_q['answer']}")
            else:
                result_placeholder.error(f"❌ 오답! 정답: {current_q['answer']}")
            if current_q.get("explanation"):
                result_placeholder.info(f"💡 이유: {current_q['explanation']}")

            # 다음 문제 준비
            quiz_state.current_idx += 1
            quiz_state.started = False
            if quiz_state.current_idx >= len(questions):
                st.success(f"게임 종료! 최종 점수: {quiz_state.score} / {len(questions)}")
            st.experimental_rerun()

        if passed:
            result_placeholder.warning(f"➡ 패스! 정답은 {current_q['answer']} 였어요.")
            quiz_state.current_idx += 1
            quiz_state.started = False
            if quiz_state.current_idx >= len(questions):
                st.success(f"게임 종료! 최종 점수: {quiz_state.score} / {len(questions)}")
            st.experimental_rerun()

        if giveup:
            quiz_state.started = False
            st.stop()

else:
    st.info("먼저 CSV를 업로드하고, 'OpenAI로 퀴즈 생성하기' 버튼을 눌러 퀴즈를 만들어주세요.")
