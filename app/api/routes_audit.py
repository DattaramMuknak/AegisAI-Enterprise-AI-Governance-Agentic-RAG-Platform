"""
/audit — query the full AI audit trail: "why did the AI produce this answer?"
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import AuditLog

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("")
def list_audit_logs(
    db: Session = Depends(get_db),
    governance_decision: Optional[str] = Query(None),
    pii_only: bool = Query(False),
    policy_violation_only: bool = Query(False),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    q = db.query(AuditLog)
    if governance_decision:
        q = q.filter(AuditLog.governance_decision == governance_decision)
    if pii_only:
        q = q.filter(AuditLog.pii_detected.is_(True))
    if policy_violation_only:
        q = q.filter(AuditLog.policy_violation.is_(True))

    total = q.count()
    rows = q.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "results": [
            {
                "id": r.id,
                "trace_id": r.trace_id,
                "prompt": r.prompt,
                "response": r.response,
                "model": r.model,
                "risk_score": r.risk_score,
                "grounding_score": r.grounding_score,
                "pii_detected": r.pii_detected,
                "policy_violation": r.policy_violation,
                "governance_decision": r.governance_decision,
                "retrieved_count": r.retrieved_count,
                "latency_ms": r.latency_ms,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in rows
        ],
    }


@router.get("/{trace_id}")
def get_audit_detail(trace_id: str, db: Session = Depends(get_db)):
    """Full 'why did the AI produce this answer' record for one request."""
    row = db.query(AuditLog).filter(AuditLog.trace_id == trace_id).first()
    if not row:
        raise HTTPException(404, "Trace not found")

    return {
        "trace_id": row.trace_id,
        "prompt": row.prompt,
        "sanitized_prompt": row.sanitized_prompt,
        "retrieved_documents": row.retrieved_documents,
        "response": row.response,
        "agent_path": row.agent_path,
        "governance": {
            "risk_score": row.risk_score,
            "grounding_score": row.grounding_score,
            "pii_detected": row.pii_detected,
            "pii_entities": row.pii_entities,
            "toxicity_score": row.toxicity_score,
            "prompt_injection_detected": row.prompt_injection_detected,
            "policy_violation": row.policy_violation,
            "policy_violation_reason": row.policy_violation_reason,
            "hallucination_flag": row.hallucination_flag,
            "governance_decision": row.governance_decision,
            "block_reason": row.block_reason,
        },
        "latency_ms": row.latency_ms,
        "token_usage": row.token_usage,
        "timestamp": row.timestamp.isoformat(),
    }
