"""Health endpoint."""


def test_health_reports_backend_and_database(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert "Traceback" not in response.text


def test_health_reports_database_outage(client, monkeypatch):
    monkeypatch.setattr("app.main.database_status", lambda: "unavailable")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_openapi_lists_phase1_endpoints(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "get" in paths["/health"]
    assert "post" in paths["/api/v1/knowledge/documents"]
    assert "get" in paths["/api/v1/knowledge/documents"]
    assert "get" in paths["/api/v1/knowledge/documents/{document_id}"]
    assert "post" in paths["/api/v1/knowledge/search"]
