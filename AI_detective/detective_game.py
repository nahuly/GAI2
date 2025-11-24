import os
import textwrap
from openai import OpenAI

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ 환경변수 OPENAI_API_KEY 가 없습니다. export 명령으로 설정하세요.")
client = OpenAI(api_key=API_KEY)

SYSTEM_PROMPT = """\
너는 논리적인 AI 탐정이다. 단서가 추가될 때마다 가설을 업데이트하라.
출력 형식:
- 유력 용의자 (이유 요약)
- 대안 가설 1~2개
- 추가로 필요한 단서
- 현재 확신도(%)
"""

def build_case_prompt(suspects, clues):
    clue_text = "- " + "\n- ".join(clues)
    return textwrap.dedent(f"""\
    사건: 사무실에서 커피 자국이 남은 컵이 발견되었다.
    용의자: {", ".join(suspects)}
    단서:
    {clue_text}
    """)

def ask_detective(suspects, clues):
    user_prompt = build_case_prompt(suspects, clues)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )
    return resp.choices[0].message.content.strip()

def main():
    print("🕵️ AI 탐정놀이 시작!\n(엔터만 누르면 종료)\n")
    suspects = ["철수(개발자)", "영희(디자이너)", "민수(인턴)"]
    clues = ["컵에는 립스틱 자국이 없다.", "커피에서 카라멜 향이 강하게 난다."]

    print("[초기 단서]")
    for c in clues:
        print("•", c)

    print("\n[AI 초기 추리]")
    print(ask_detective(suspects, clues))

    while True:
        new_clue = input("\n새 단서 입력 (엔터 시 종료): ").strip()
        if not new_clue:
            print("\n게임 종료! 🎬")
            break
        clues.append(new_clue)
        print("\n[AI 추리 갱신]")
        print(ask_detective(suspects, clues))

if __name__ == "__main__":
    main()
