"""API REST del agente de triage."""
import hashlib
import hmac
import logging
import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.agent import build_graph, mcp_connection, triage
from app.guardrails import GuardrailError
from app.schemas import IssueInput, TriageResult
from app.security import rate_limit

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Se ejecuta una vez al arrancar: carga las herramientas MCP y construye el grafo."""
    client = MultiServerMCPClient(mcp_connection())
    app.state.graph = build_graph(await client.get_tools())
    yield


app = FastAPI(title="IssueTriage AI", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResult, dependencies=[Depends(rate_limit)])
async def triage_issue(issue: IssueInput, session_id: str | None = None):
    try:
        out = await triage(issue.title, issue.body, session_id=session_id, graph=app.state.graph)
    except GuardrailError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return out["result"]

def verify_signature(body: bytes, signature: str | None):
    """Comprueba que el webhook venga de GitHub: HMAC-SHA256 del cuerpo con el secreto compartido."""
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not secret or not signature or not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


async def triage_in_background(issue):
    try:
        out = await triage(issue["title"], issue.get("body") or "",
                        session_id=f"issue-{issue['number']}", graph=app.state.graph)
        log.info("Issue #%s triaged as %s", issue["number"], out["result"].label)
    except GuardrailError as e:
        log.warning("Issue #%s rejected: %s", issue["number"], e)


@app.post("/webhooks/github", status_code=202)
async def github_webhook(request: Request, background: BackgroundTasks,
                        x_hub_signature_256: str | None = Header(None),
                        x_github_event: str | None = Header(None)):
    body = await request.body()
    verify_signature(body, x_hub_signature_256)
    payload = await request.json()
    if x_github_event != "issues" or payload.get("action") != "opened":
        return {"status": "ignored"}
    background.add_task(triage_in_background, payload["issue"])
    return {"status": "accepted", "issue": payload["issue"]["number"]}