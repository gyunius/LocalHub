import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.mark.asyncio
async def test_chat_mock():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post('/api/chat', json={"message": "test"})
        assert r.status_code == 200
        data = r.json()
        assert 'reply' in data

@pytest.mark.asyncio
async def test_chat_openai_fallback():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post('/api/chat_openai', json={"message": "test"})
        assert r.status_code == 200
        data = r.json()
        assert 'reply' in data
