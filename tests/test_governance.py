"""
Unit and Integration Tests for AegisAI Platform
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify system health endpoint returns 200 and ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_root_endpoint():
    """Verify root endpoint returns API description and docs link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "AegisAI" in data.get("message", "")
    assert data.get("docs") == "/docs"


def test_mlflow_tracker_import():
    """Verify MLflow tracker module can be imported and initialized gracefully."""
    from app.tracking.mlflow_tracker import log_request

    # Test best-effort logging fallback (swallows exceptions when MLflow server unavailable)
    sample_result = {
        "governance": {
            "governance_decision": "PASS",
            "risk_score": 0.05,
            "grounding_score": 0.98,
            "toxicity_score": 0.01,
            "pii_detected": False,
            "policy_violation": False,
            "hallucination_flag": False,
        },
        "agent_path": ["router", "compliance", "response"],
        "latency_ms": 120,
        "sources": [],
        "token_usage": {"prompt": 50, "completion": 30},
    }

    # Should complete without error even if MLflow backend is unreachable
    log_request(trace_id="test-trace-123", result=sample_result)
