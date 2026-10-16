import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database.session import init_db

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Vidora"

async def test_capabilities(client):
    response = await client.get("/api/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["ffmpeg_available"] is True
    assert data["ffprobe_available"] is True
    assert "mp4" in data["supported_video_containers"]
    assert "mp3" in data["supported_audio_containers"]

async def test_analyze_valid_mock_url(client):
    response = await client.post("/api/video/analyze", json={"url": "https://test-media.local/watch?v=mock_video"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    meta = data["data"]
    assert meta["title"] == "Vidora Sample Showcase Video"
    assert len(meta["video_options"]) > 0
    assert len(meta["audio_options"]) > 0

async def test_analyze_blocked_ssrf_url(client):
    response = await client.post("/api/video/analyze", json={"url": "http://127.0.0.1:8000/api/secret"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "blocked" in data["error"].lower() or "unauthorized" in data["error"].lower()

async def test_create_download_and_poll_status(client):
    payload = {
        "url": "https://test-media.local/watch?v=mock_video",
        "mode": "video_audio",
        "resolution": "720p",
        "target_container": "mp4"
    }
    response = await client.post("/api/downloads", json=payload)
    assert response.status_code == 202
    job = response.json()
    job_id = job["job_id"]
    assert job_id.startswith("job_")

    # Poll status
    status_resp = await client.get(f"/api/downloads/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ("queued", "analyzing", "downloading", "merging", "completed")

async def test_search_endpoint(client):
    response = await client.get("/api/video/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert isinstance(data["results"], list)
