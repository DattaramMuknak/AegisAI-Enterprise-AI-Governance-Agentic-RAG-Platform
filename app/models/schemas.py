"""
Pydantic schemas for API request/response contracts.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    user_id: Optional[str] = None
    top_k: int = Field(default=4, ge=1, le=20)


class RetrievedSource(BaseModel):
    doc_id: str
    filename: Optional[str] = None
    chunk: str
    score: float


class GovernanceReport(BaseModel):
    risk_score: int
    grounding_score: float
    pii_detected: bool
    pii_entities: List[str] = []
    toxicity_score: float
    prompt_injection_detected: bool
    policy_violation: bool
    policy_violation_reason: Optional[str] = None
    hallucination_flag: bool
    governance_decision: str
    block_reason: Optional[str] = None
    confidence: str  # High | Medium | Low


class ChatResponse(BaseModel):
    trace_id: str
    answer: Optional[str]
    sources: List[RetrievedSource]
    governance: GovernanceReport
    agent_path: List[str]
    latency_ms: int
    token_usage: Dict[str, Any] = {}


class DashboardStats(BaseModel):
    total_requests: int
    blocked_requests: int
    pii_incidents: int
    hallucination_flags: int
    policy_violations: int
    average_risk_score: float
    average_latency_ms: float
    average_grounding_score: float


class AuditLogOut(BaseModel):
    id: str
    trace_id: str
    prompt: str
    response: Optional[str]
    model: Optional[str]
    risk_score: int
    grounding_score: float
    pii_detected: bool
    policy_violation: bool
    governance_decision: str
    retrieved_count: int
    latency_ms: int
    timestamp: str

    class Config:
        from_attributes = True
