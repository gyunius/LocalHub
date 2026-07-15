import pytest
from httpx import AsyncClient
import sys, os
# ensure repo root is on sys.path so `backend` package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.mark.asyncio
async def test_pois_search_returns_items():
    from backend.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/api/pois?limit=2")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_chat_mock_search_integration():
    from backend.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"message": "한강 공원 추천"}
        r = await ac.post("/api/chat", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "reply" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)