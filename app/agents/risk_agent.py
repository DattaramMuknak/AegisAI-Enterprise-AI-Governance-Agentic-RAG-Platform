"""
Risk Agent — combines toxicity scoring + hallucination/grounding checks +
compliance signals into a single AI Risk Score and a governance decision.
"""
from typing import List

from app.core.config import settings
from app.governance import hallucination, risk_scorer, toxicity


def assess(
    prompt: str,
    response: str,
    retrieved_chunks: List[str],
    injection_detected: bool,
    injection_matches: List[str],
    pii_count: int,
    policy_violation: bool,
) -> dict:
    tox_score = toxicity.score(f"{prompt}\n{response}")
    grounding = hallucination.grounding_score(response, retrieved_chunks)
    hallucination_flag = hallucination.is_hallucination(
        response, retrieved_chunks, settings.GROUNDING_MIN_SCORE
    )

    injection_points = 0
    if injection_detected:
        from app.governance.prompt_injection import injection_risk_contribution
        injection_points = injection_risk_contribution(prompt)

    inputs = risk_scorer.RiskInputs(
        prompt_injection_detected=injection_detected,
        injection_points=injection_points,
        toxicity_score=tox_score,
        pii_count=pii_count,
        grounding_score=grounding,
        policy_violation=policy_violation,
    )
    result = risk_scorer.compute(inputs)
    decision, block_reason = risk_scorer.decide(
        result.risk_score, settings.RISK_BLOCK_THRESHOLD, policy_violation
    )
    confidence = hallucination.confidence_label(grounding, result.risk_score)

    return {
        "risk_score": result.risk_score,
        "breakdown": result.breakdown,
        "toxicity_score": tox_score,
        "grounding_score": grounding,
        "hallucination_flag": hallucination_flag,
        "governance_decision": decision,
        "block_reason": block_reason,
        "confidence": confidence,
    }
