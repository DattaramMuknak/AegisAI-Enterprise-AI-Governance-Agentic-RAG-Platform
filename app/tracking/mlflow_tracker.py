"""
MLflow tracking — logs every governed AI request as an MLflow run so risk
scores, grounding scores, latency, and token usage are trackable/queryable
over time and comparable across model/prompt versions.
"""
from contextlib import contextmanager

import mlflow

from app.core.config import settings

_initialized = False


def _init():
    global _initialized
    if _initialized:
        return
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)
    _initialized = True


def log_request(trace_id: str, result: dict) -> None:
    """Best-effort logging — governance decisions must never fail because
    the tracking backend is unreachable, so failures are swallowed."""
    try:
        _init()
        governance = result["governance"]
        with mlflow.start_run(run_name=trace_id):
            mlflow.log_param("model", settings.GROQ_MODEL)
            mlflow.log_param("governance_decision", governance["governance_decision"])
            mlflow.log_param("agent_path", ",".join(result["agent_path"]))

            mlflow.log_metric("risk_score", governance["risk_score"])
            mlflow.log_metric("grounding_score", governance["grounding_score"])
            mlflow.log_metric("toxicity_score", governance["toxicity_score"])
            mlflow.log_metric("latency_ms", result["latency_ms"])
            mlflow.log_metric("retrieved_count", len(result.get("sources", [])))

            token_usage = result.get("token_usage", {})
            for k, v in token_usage.items():
                mlflow.log_metric(f"tokens_{k}", v)

            mlflow.set_tag("pii_detected", governance["pii_detected"])
            mlflow.set_tag("policy_violation", governance["policy_violation"])
            mlflow.set_tag("hallucination_flag", governance["hallucination_flag"])
    except Exception as e:  # noqa: BLE001
        print(f"[mlflow_tracker] logging skipped: {e}")


@contextmanager
def trace_span(name: str):
    """Small helper for wrapping arbitrary blocks with an MLflow nested run."""
    try:
        _init()
        with mlflow.start_run(run_name=name, nested=True) as run:
            yield run
    except Exception as e:  # noqa: BLE001
        print(f"[mlflow_tracker] span skipped: {e}")
        yield None
