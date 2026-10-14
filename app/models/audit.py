"""
SQLAlchemy ORM models — this is the audit backbone of the platform.
Every AI request/response cycle is persisted here so an org can answer
"why did the AI produce this answer?" after the fact.
"""
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer")  # admin | analyst | viewer
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=_uuid)
    filename = Column(String(500), nullable=False)
    source_type = Column(String(50))  # policy | sop | contract | manual
    chunk_count = Column(Integer, default=0)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="processed")  # processing | processed | failed


class AuditLog(Base):
    """
    One row per AI request. This is the table the Governance Dashboard
    and 'why did the AI say this' queries are built on.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=_uuid)
    trace_id = Column(String(36), default=_uuid, index=True)

    # Who / what
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    prompt = Column(Text, nullable=False)
    sanitized_prompt = Column(Text, nullable=True)  # after PII redaction
    model = Column(String(100))

    # Retrieval
    retrieved_documents = Column(JSON, default=list)  # list of {doc_id, chunk, score}
    retrieved_count = Column(Integer, default=0)

    # Response
    response = Column(Text, nullable=True)
    agent_path = Column(JSON, default=list)  # e.g. ["router","retrieval","compliance","risk","response"]

    # Governance signals
    risk_score = Column(Integer, default=0)          # 0-100
    grounding_score = Column(Float, default=0.0)      # 0-1
    pii_detected = Column(Boolean, default=False)
    pii_entities = Column(JSON, default=list)
    toxicity_score = Column(Float, default=0.0)
    prompt_injection_detected = Column(Boolean, default=False)
    policy_violation = Column(Boolean, default=False)
    policy_violation_reason = Column(Text, nullable=True)
    hallucination_flag = Column(Boolean, default=False)

    governance_decision = Column(String(50), default="allowed")  # allowed | blocked | redacted | escalated
    block_reason = Column(Text, nullable=True)

    # Ops
    latency_ms = Column(Integer, default=0)
    token_usage = Column(JSON, default=dict)  # {prompt_tokens, completion_tokens, total_tokens}

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")
