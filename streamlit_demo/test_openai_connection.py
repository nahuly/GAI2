import os
from openai import OpenAI

raw_key = os.getenv("OPENAI_API_KEY") or ""
api_key = raw_key.strip()  # 👈 공백/줄바꿈 제거

print("OPENAI_API_KEY(raw):", repr(raw_key))
print("OPENAI_API_KEY(stripped):", repr(api_key))

client = OpenAI(api_key=api_key)

try:
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": "ping"}],
    )
    print("✅ 연결 성공")
    print("응답:", completion.choices[0].message.content)
except Exception as e:
    print("❌ 연결 실패")
    print(type(e))
    print(e)
