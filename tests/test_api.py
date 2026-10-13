import pytest
from fastapi.testclient import TestClient
from agents.api import app

client = TestClient(app)

CASE = {
    "task_id": "TASK-001",
    "target_identifier": "SPEC-001",
    "primary_metric": 30.0,
    "secondary_metric": 13.0,
    "status_descriptor": "DISCORDANT",
    "is_critical_flag": True,
}


def test_api_audit_and_health(monkeypatch):
    monkeypatch.delenv("MTB_API_TOKEN", raising=False)
    assert client.get("/health").status_code == 200
    res = client.post("/api/audit", json=CASE)
    assert res.status_code == 200
    dossier = res.json()
    assert dossier["total_alerts"] == 3
    assert dossier["critical_alerts_count"] == 1


def test_api_phi_rejection_is_client_error(monkeypatch):
    monkeypatch.delenv("MTB_API_TOKEN", raising=False)
    payload = {**CASE, "target_identifier": "MRN-994827"}
    res = client.post("/api/audit", json=payload)
    assert res.status_code == 422
    assert "MRN-994827" not in res.text


def test_audit_logs_require_configured_token(monkeypatch):
    monkeypatch.delenv("MTB_API_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 503
    monkeypatch.setenv("MTB_API_TOKEN", "test-bearer-secret")
    assert client.get("/api/audit/logs").status_code == 401
    res = client.get("/api/audit/logs", headers={"Authorization": "Bearer test-bearer-secret"})
    assert res.status_code == 200
    assert res.json()["verified"] is True


def test_token_guards_audit_and_chat(monkeypatch):
    monkeypatch.setenv("MTB_API_TOKEN", "test-token")
    assert client.post("/api/audit", json=CASE).status_code == 401
    assert client.post("/api/chat", json={"query": "status"}).status_code == 401
    assert client.post("/api/audit", json=CASE, headers={"Authorization": "Bearer test-token"}).status_code == 200
    assert client.post("/api/chat", json={"query": "status"}, headers={"Authorization": "Bearer test-token"}).status_code == 200
