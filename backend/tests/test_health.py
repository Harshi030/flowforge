from fastapi.testclient import TestClient
import pytest

def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers
    
def test_ready_returns_503_when_dependencies_down(client: TestClient,monkeypatch:pytest.MonkeyPatch) -> None:
    def broken_session() -> None:
        raise ConnectionError("db down")
      
    def broken_redis() -> None:
      raise ConnectionError("redis down")
    
    monkeypatch.setattr("app.api.health.SessionLocal", broken_session)
    monkeypatch.setattr("app.api.health.redis.Redis.from_url",broken_redis)
    
    response = client.get("/ready")
    
    assert response.status_code == 503
    assert response.json() == {"database":"unavailable", "redis":"unavailable"}

