import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

samples = [
    "서울 남산타워 근처 가족이 갈 만한 곳 추천해줘",
    "서울에서 야경 보기 좋은 장소 알려줘",
    "아이와 함께 갈 수 있는 박물관 추천해줘",
]

for i, msg in enumerate(samples, 1):
    resp = client.post("/api/chat_openai", json={"message": msg, "top_k": 3, "use_search": True})
    print(f"--- Sample {i} ---")
    print("Request:", msg)
    try:
        print("Status:", resp.status_code)
        print("Response:", resp.json())
    except Exception as e:
        print("Failed to parse response:", e)
    print()
