"""FastAPI interface for the local rule-based demonstrator.

Set MTB_API_TOKEN for authenticated API usage. Audit-log access is disabled
unless that token is configured.
"""
import os
import secrets

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="MTB Orchestrator Pro API",
    description="Rule-based demonstration workers; not validated clinical decision support.",
    version="2.0.1",
)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


def _check_token(authorization: str, required: bool = False) -> None:
    token = os.getenv("MTB_API_TOKEN", "")
    if required and not token:
        raise HTTPException(status_code=503, detail="This endpoint requires MTB_API_TOKEN configuration.")
    if token and not secrets.compare_digest(authorization, f"Bearer {token}"):
        raise HTTPException(status_code=401, detail="Valid bearer token required.")


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "mtb-orchestrator-pro", "mode": "DEMONSTRATION", "version": "2.0.1"}


@app.get("/metrics")
def metrics(authorization: str = Header(default="")):
    _check_token(authorization)
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload, authorization: str = Header(default="")):
    _check_token(authorization)
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException:
        raise HTTPException(status_code=422, detail="A direct identifier was detected. Use synthetic input.") from None


@app.post("/api/chat")
def api_chat(req: ChatRequest, authorization: str = Header(default="")):
    _check_token(authorization)
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException:
        raise HTTPException(status_code=422, detail="A direct identifier was detected. Use synthetic input.") from None


@app.get("/api/audit/logs")
def api_audit_logs(authorization: str = Header(default="")):
    _check_token(authorization, required=True)
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
