# streamlit_detective.py
import os
import textwrap
import time
import uuid
from typing import List, Dict
import streamlit as st
from openai import OpenAI

# ----------------------------
# 기본 설정 & 클라이언트 준비
# ----------------------------
st.set_page_config(page_title="AI 탐정놀이", page_icon="🕵️", layout="centered")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("환경변수 OPENAI_API_KEY가 없습니다. 터미널에서 `export OPENAI_API_KEY='sk-...'` 설정 후 다시 실행하세요.")
    st.stop()

client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """\
너는 논리적인 AI 탐정이다. 단서가 추가될 때마다 가설을 업데이트하라.
출력 형식(간결, bullet 권장):
- 유력 용의자(이유 요약)
- 대안 가설 1~2개
- 추가로 필요한 단서
- 현재 확신도(%)
규칙:
- 제공되지 않은 사실은 단정하지 말 것
- 단서는 항상 최신 상태로 종합하여 판단할 것
"""

# --------------------------------
# 유틸: 프롬프트 빌더 / 모델 호출
# --------------------------------
def build_case_prompt(case_title: str, suspects: List[str], clues: List[str]) -> str:
    clue_text = "- " + "\n- ".join(clues) if clues else "(아직 단서 없음)"
    body = f"""사건: {case_title}
용의자: {", ".join(suspects)}
단서:
{clue_text}
"""
    # dedent로 들여쓰기 정리
    return textwrap.dedent(body)

def ask_detective(case_title: str, suspects: List[str], clues: List[str], temperature: float = 0.3) -> str:
    user_prompt = build_case_prompt(case_title, suspects, clues)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()

# ----------------------------
# 세션 상태 초기화
# ----------------------------
if "case_id" not in st.session_state:
    st.session_state.case_id = str(uuid.uuid4())  # 로그/히스토리 키용
if "case_title" not in st.session_state:
    st.session_state.case_title = "사무실에서 커피 자국이 남은 컵이 발견되었다."
if "suspects" not in st.session_state:
    st.session_state.suspects = ["철수(개발자)", "영희(디자이너)", "민수(인턴)"]
if "clues" not in st.session_state:
    st.session_state.clues = ["컵에는 립스틱 자국이 없다.", "커피에서 카라멜 향이 강하다."]
if "history" not in st.session_state:
    st.session_state.history = []  # [{step, clues, result, timestamp}]

# ----------------------------
# 사이드바: 사건 프리셋/설정
# ----------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    preset = st.selectbox(
        "프리셋 사건 고르기",
        [
            "커피 컵 사건(기본)",
            "사라진 키보드 사건",
            "회의실 빔프로젝터 리모컨 실종",
        ],
        index=0,
    )

    if st.button("프리셋 적용"):
        if preset == "커피 컵 사건(기본)":
            st.session_state.case_title = "사무실에서 커피 자국이 남은 컵이 발견되었다."
            st.session_state.suspects = ["철수(개발자)", "영희(디자이너)", "민수(인턴)"]
            st.session_state.clues = ["컵에는 립스틱 자국이 없다.", "커피에서 카라멜 향이 강하다."]
        elif preset == "사라진 키보드 사건":
            st.session_state.case_title = "공용 키보드가 사무실에서 사라졌다."
            st.session_state.suspects = ["A(프론트엔드)", "B(백엔드)", "C(인턴)"]
            st.session_state.clues = ["전날 야근조가 있었다.", "C는 개인 키보드를 집에 두고 다닌다."]
        else:
            st.session_state.case_title = "회의실 빔프로젝터 리모컨이 실종되었다."
            st.session_state.suspects = ["기획자", "디자이너", "개발자"]
            st.session_state.clues = ["회의 끝나고 급하게 나갔다.", "화이트보드 마커가 책상에 흩어져 있었다."]
        st.session_state.history.clear()
        st.success("프리셋이 적용되었습니다!")

    st.divider()
    st.caption("🔐 OPENAI_API_KEY는 환경변수로 읽습니다.")
    temp = st.slider("창의성(temperature)", 0.0, 1.0, 0.3, 0.1)

# ----------------------------
# 본문 UI
# ----------------------------
st.title("🕵️ AI 탐정놀이")
st.write("단서를 추가하면서 **AI의 추론 업데이트**를 관찰해보세요!")

# 사건 제목
st.subheader("📌 사건")
st.text_input("사건 설명", value=st.session_state.case_title, key="case_title")

# 용의자 편집
st.subheader("👤 용의자")
suspect_cols = st.columns(3)
for i in range(3):
    key = f"suspect_{i}"
    default = st.session_state.suspects[i] if i < len(st.session_state.suspects) else ""
    st.session_state.suspects[i:i+1] = [suspect_cols[i].text_input(f"용의자 {i+1}", value=default)]

# 단서 리스트
st.subheader("🧩 단서")
for idx, c in enumerate(st.session_state.clues):
    st.write(f"• {c}")

new_clue = st.text_input("새 단서 입력", placeholder="예) 컵 근처에서 디자이너 스케치북 발견")
clue_cols = st.columns(3)
add_clicked = clue_cols[0].button("➕ 단서 추가")
undo_clicked = clue_cols[1].button("↩️ 마지막 단서 취소")
reset_clicked = clue_cols[2].button("🧹 초기화")

if add_clicked and new_clue.strip():
    st.session_state.clues.append(new_clue.strip())
    st.success("단서가 추가되었습니다!")

if undo_clicked and st.session_state.clues:
    removed = st.session_state.clues.pop()
    st.info(f"마지막 단서 취소: {removed}")

if reset_clicked:
    st.session_state.clues = []
    st.session_state.history.clear()
    st.warning("단서와 히스토리를 초기화했습니다.")

st.divider()

# 추리 실행 버튼
run = st.button("🧠 AI 추리 갱신")

# 결과 영역
if run:
    with st.spinner("AI가 추리 중..."):
        result = ask_detective(
            case_title=st.session_state.case_title,
            suspects=st.session_state.suspects,
            clues=st.session_state.clues,
            temperature=temp,
        )
        st.session_state.history.append({
            "step": len(st.session_state.history) + 1,
            "clues": list(st.session_state.clues),
            "result": result,
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

# 히스토리 타임라인
st.subheader("🗂️ 추리 히스토리")
if not st.session_state.history:
    st.caption("아직 실행 기록이 없습니다. 단서를 추가하고 **AI 추리 갱신**을 눌러보세요.")
else:
    for h in reversed(st.session_state.history):
        with st.expander(f"[Step {h['step']}] {h['ts']} — 단서 {len(h['clues'])}개"):
            st.markdown("**단서 목록**")
            for c in h["clues"]:
                st.write("•", c)
            st.markdown("**AI 추리 결과**")
            st.write(h["result"])

# 다운로드(선택)
if st.session_state.history:
    if st.download_button(
        "📥 결과 내보내기 (txt)",
        data="\n\n".join(
            f"[Step {h['step']}] {h['ts']}\n"
            + "단서:\n- " + "\n- ".join(h["clues"]) + "\n\n"
            + "결과:\n" + h["result"]
            for h in st.session_state.history
        ),
        file_name="ai_detective_history.txt",
        mime="text/plain",
    ):
        st.toast("내보내기 완료!", icon="✅")
