"""
/chat — the main AI Gateway endpoint. Runs the full agentic governance
pipeline and persists every request to the audit log.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.router_agent import run_pipeline
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.schemas import ChatRequest, ChatResponse, GovernanceReport, RetrievedSource
from app.tracking.mlflow_tracker import log_request

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    result = run_pipeline(request.prompt, top_k=request.top_k)

    # Persist to audit trail (MySQL) — the "why did the AI say this" record
    log_entry = AuditLog(
        trace_id=result["trace_id"],
        user_id=request.user_id,
        prompt=request.prompt,
        sanitized_prompt=result.get("sanitized_prompt"),
        model="groq",
        retrieved_documents=result["sources"],
        retrieved_count=len(result["sources"]),
        response=result["answer"],
        agent_path=result["agent_path"],
        risk_score=result["governance"]["risk_score"],
        grounding_score=result["governance"]["grounding_score"],
        pii_detected=result["governance"]["pii_detected"],
        pii_entities=result["governance"]["pii_entities"],
        toxicity_score=result["governance"]["toxicity_score"],
        prompt_injection_detected=result["governance"]["prompt_injection_detected"],
        policy_violation=result["governance"]["policy_violation"],
        policy_violation_reason=result["governance"]["policy_violation_reason"],
        hallucination_flag=result["governance"]["hallucination_flag"],
        governance_decision=result["governance"]["governance_decision"],
        block_reason=result["governance"]["block_reason"],
        latency_ms=result["latency_ms"],
        token_usage=result["token_usage"],
    )
    db.add(log_entry)
    db.commit()

    # Fire-and-forget style experiment tracking
    log_request(result["trace_id"], result)

    return ChatResponse(
        trace_id=result["trace_id"],
        answer=result["answer"],
        sources=[RetrievedSource(**s) for s in result["sources"]],
        governance=GovernanceReport(**result["governance"]),
        agent_path=result["agent_path"],
        latency_ms=result["latency_ms"],
        token_usage=result["token_usage"],
    )
