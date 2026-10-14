"""
/dashboard — aggregate governance metrics, mirroring the product spec:

  Total AI Requests, Blocked Requests, PII Incidents, Hallucination Flags,
  Policy Violations, Average Risk Score, Average Latency.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.schemas import DashboardStats

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(AuditLog.id)).scalar() or 0
    blocked = db.query(func.count(AuditLog.id)).filter(
        AuditLog.governance_decision == "blocked"
    ).scalar() or 0
    pii = db.query(func.count(AuditLog.id)).filter(AuditLog.pii_detected.is_(True)).scalar() or 0
    hallucinations = db.query(func.count(AuditLog.id)).filter(
        AuditLog.hallucination_flag.is_(True)
    ).scalar() or 0
    policy = db.query(func.count(AuditLog.id)).filter(
        AuditLog.policy_violation.is_(True)
    ).scalar() or 0

    avg_risk = db.query(func.avg(AuditLog.risk_score)).scalar() or 0.0
    avg_latency = db.query(func.avg(AuditLog.latency_ms)).scalar() or 0.0
    avg_grounding = db.query(func.avg(AuditLog.grounding_score)).scalar() or 0.0

    return DashboardStats(
        total_requests=total,
        blocked_requests=blocked,
        pii_incidents=pii,
        hallucination_flags=hallucinations,
        policy_violations=policy,
        average_risk_score=round(float(avg_risk), 2),
        average_latency_ms=round(float(avg_latency), 2),
        average_grounding_score=round(float(avg_grounding), 3),
    )


@router.get("/timeseries")
def get_timeseries(db: Session = Depends(get_db), days: int = 14):
    """Daily request volume + average risk score for the last N days."""
    rows = (
        db.query(
            func.date(AuditLog.timestamp).label("day"),
            func.count(AuditLog.id).label("requests"),
            func.avg(AuditLog.risk_score).label("avg_risk"),
            func.sum(func.cast(AuditLog.governance_decision == "blocked", type_=__import__("sqlalchemy").Integer)).label("blocked"),
        )
        .group_by(func.date(AuditLog.timestamp))
        .order_by(func.date(AuditLog.timestamp).desc())
        .limit(days)
        .all()
    )
    return [
        {
            "day": str(r.day),
            "requests": r.requests,
            "avg_risk_score": round(float(r.avg_risk or 0), 2),
            "blocked": int(r.blocked or 0),
        }
        for r in reversed(rows)
    ]
