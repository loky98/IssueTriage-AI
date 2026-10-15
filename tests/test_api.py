import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.guardrails import GuardrailError
from app.schemas import TriageResult
from app.security import rate_limit, require_api_key

FAKE = TriageResult(reasoning="r", label="Bug", confidence=0.9, suggested_reply="x", needs_human=False)
ISSUE = {"title": "read_csv bug", "body": "pd.read_csv fails"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_KEYS", "test-key")
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    calls = []

    async def fake_triage(title, body, **kwargs):  # reemplaza al agente: sin LLM ni MCP
        calls.append(title)
        return {"result": FAKE}

    monkeypatch.setattr(main, "triage", fake_triage)
    main.app.dependency_overrides[rate_limit] = require_api_key  # auth sí, Redis no
    main.app.state.graph = None
    yield TestClient(main.app), calls  # sin "with": no ejecuta el lifespan (no arranca MCP)
    main.app.dependency_overrides.clear()


def sign(body):
    return "sha256=" + hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()


def test_health(client):
    c, _ = client
    assert c.get("/health").json() == {"status": "ok"}


def test_triage_requires_api_key(client):
    c, _ = client
    assert c.post("/triage", json=ISSUE).status_code == 401
    assert c.post("/triage", json=ISSUE, headers={"X-API-Key": "bad"}).status_code == 401


def test_triage_returns_result(client):
    c, _ = client
    r = c.post("/triage", json=ISSUE, headers={"X-API-Key": "test-key"})
    assert r.status_code == 200 and r.json()["label"] == "Bug"


def test_guardrail_rejection_returns_422(client, monkeypatch):
    c, _ = client

    async def reject(*args, **kwargs):
        raise GuardrailError("Out of domain")

    monkeypatch.setattr(main, "triage", reject)
    assert c.post("/triage", json=ISSUE, headers={"X-API-Key": "test-key"}).status_code == 422


def test_webhook_checks_signature_and_triggers_triage(client):
    c, calls = client
    body = json.dumps({"action": "opened", "issue": {"number": 1, "title": "groupby bug", "body": ""}}).encode()
    headers = {"Content-Type": "application/json", "X-GitHub-Event": "issues"}
    bad = c.post("/webhooks/github", content=body, headers={**headers, "X-Hub-Signature-256": "sha256=bad"})
    assert bad.status_code == 401
    ok = c.post("/webhooks/github", content=body, headers={**headers, "X-Hub-Signature-256": sign(body)})
    assert ok.status_code == 202 and calls == ["groupby bug"]