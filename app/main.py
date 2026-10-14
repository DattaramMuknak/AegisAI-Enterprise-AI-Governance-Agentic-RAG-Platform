"""
AegisAI — Enterprise AI Governance & Agentic RAG Platform
FastAPI application entrypoint (the "AI Gateway" in the architecture diagram).
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_audit, routes_auth, routes_chat, routes_dashboard, routes_documents
from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("aegisai")

app = FastAPI(
    title="AegisAI — Enterprise AI Governance & Agentic RAG Platform",
    description=(
        "Governed RAG platform: Router Agent -> Retrieval Agent -> "
        "Compliance Agent -> Risk Agent -> Response Agent, with full "
        "audit logging, PII redaction, prompt-injection defense, "
        "hallucination/grounding checks, and policy enforcement."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_chat.router)
app.include_router(routes_documents.router)
app.include_router(routes_dashboard.router)
app.include_router(routes_audit.router)


@app.on_event("startup")
def on_startup():
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.ENV)
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


@app.get("/")
def root():
    return {
        "message": "AegisAI Governance & Compliance Copilot is running.",
        "docs": "/docs",
        "dashboard_api": "/api/v1/dashboard/stats",
    }
