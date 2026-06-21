"""Tests for the /health endpoint (M1 definition of done: health check passes)."""


def test_health_returns_200_ok(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_status_ok_body(client):
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
