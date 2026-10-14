"""
Compliance Agent — runs PII detection, prompt-injection detection, and
policy checks against the incoming prompt (pre-generation gate) and,
after generation, against the drafted response too.
"""
from dataclasses import dataclass, field
from typing import List

from app.governance import pii_detector, policy_checker, prompt_injection


@dataclass
class ComplianceReport:
    sanitized_prompt: str
    pii_detected: bool
    pii_entities: List[str] = field(default_factory=list)
    injection_detected: bool = False
    injection_matches: List[str] = field(default_factory=list)
    policy_violation: bool = False
    policy_reason: str | None = None


def review_prompt(prompt: str) -> ComplianceReport:
    sanitized, findings = pii_detector.pii_detector.redact(prompt)
    injection_flag, injection_matches = prompt_injection.detect(prompt)
    policy_flag, policy_reason = policy_checker.check(prompt)

    return ComplianceReport(
        sanitized_prompt=sanitized,
        pii_detected=len(findings) > 0,
        pii_entities=[f.entity_type for f in findings],
        injection_detected=injection_flag,
        injection_matches=injection_matches,
        policy_violation=policy_flag,
        policy_reason=policy_reason,
    )


def review_response(prompt: str, response: str) -> tuple:
    """Second-pass policy check including the generated response."""
    policy_flag, policy_reason = policy_checker.check(prompt, response)
    return policy_flag, policy_reason
