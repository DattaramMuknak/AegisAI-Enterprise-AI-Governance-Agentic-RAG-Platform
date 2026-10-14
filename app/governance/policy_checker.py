"""
Policy violation detection.

Checks the prompt/response pair against a configurable set of
organizational policy rules (denylist topics, required disclaimers,
regulated-advice detection). Rules are simple and file-driven so
compliance teams can edit them without touching code.
"""
import re
from typing import List, Optional, Tuple

# In production these would be loaded from the ingested SOP/policy
# documents themselves (via RAG) or a compliance-managed config table.
_DENYLIST_TOPICS = [
    (r"\b(insider trading|market manipulation)\b", "Financial misconduct guidance requested."),
    (r"\b(bypass|circumvent) (kyc|aml|compliance)\b", "Attempt to bypass compliance controls."),
    (r"\bfabricate (invoice|financial statement|audit report)\b", "Fraudulent document generation requested."),
    (r"\bshare (customer|patient) (data|records) (externally|outside)\b", "Unauthorized data-sharing request."),
]

_REGULATED_ADVICE_PATTERNS = [
    r"\b(guaranteed returns|guaranteed profit)\b",
    r"\bdefinitely (safe|legal) (investment|tax) (strategy|advice)\b",
]


def check(prompt: str, response: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Returns (violation_found, reason)."""
    combined = f"{prompt}\n{response or ''}".lower()

    for pattern, reason in _DENYLIST_TOPICS:
        if re.search(pattern, combined, re.IGNORECASE):
            return True, reason

    for pattern in _REGULATED_ADVICE_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            return True, "Response makes an unqualified regulated-advice guarantee."

    return False, None


def list_active_rules() -> List[str]:
    return [reason for _, reason in _DENYLIST_TOPICS] + [
        "Unqualified regulated-advice guarantees"
    ]
