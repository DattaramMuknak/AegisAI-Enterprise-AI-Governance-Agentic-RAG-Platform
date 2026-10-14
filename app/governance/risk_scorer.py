"""
Aggregate AI Risk Score.

Combines every governance signal into a single 0-100 score, mirroring the
"AI Risk Score: 18/100" style output described in the product spec. Kept
as simple weighted arithmetic (not a black box) so the audit trail can
show a human exactly why a score was produced.
"""
from dataclasses import dataclass, field


@dataclass
class RiskInputs:
    prompt_injection_detected: bool
    injection_points: int
    toxicity_score: float               # 0-1
    pii_count: int
    grounding_score: float              # 0-1 (higher = safer)
    policy_violation: bool


@dataclass
class RiskResult:
    risk_score: int
    breakdown: dict = field(default_factory=dict)


def compute(inputs: RiskInputs) -> RiskResult:
    breakdown = {}

    injection_points = inputs.injection_points if inputs.prompt_injection_detected else 0
    breakdown["prompt_injection"] = injection_points

    toxicity_points = round(inputs.toxicity_score * 30)
    breakdown["toxicity"] = toxicity_points

    pii_points = min(inputs.pii_count * 8, 25)
    breakdown["pii_exposure"] = pii_points

    # Poor grounding (potential hallucination) contributes up to 30 points
    hallucination_points = round((1 - inputs.grounding_score) * 30)
    breakdown["hallucination_risk"] = hallucination_points

    policy_points = 35 if inputs.policy_violation else 0
    breakdown["policy_violation"] = policy_points

    total = sum(breakdown.values())
    total = max(0, min(total, 100))

    return RiskResult(risk_score=total, breakdown=breakdown)


def decide(risk_score: int, block_threshold: int, policy_violation: bool) -> tuple:
    """Returns (governance_decision, block_reason)."""
    if policy_violation:
        return "blocked", "Policy violation detected."
    if risk_score >= block_threshold:
        return "blocked", f"AI Risk Score {risk_score} exceeded threshold {block_threshold}."
    if risk_score >= block_threshold * 0.6:
        return "escalated", "Elevated risk score — flagged for human review."
    return "allowed", None
