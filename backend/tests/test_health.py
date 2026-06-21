"""Health endpoint test — verifies the app boots and create_all runs on startup."""


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
