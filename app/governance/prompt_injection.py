"""
Prompt injection / jailbreak detection.

Heuristic + pattern-based detector. Good enough as a first line of defense
in front of the LLM call; can be swapped for a fine-tuned classifier later
without changing the interface (`detect(text) -> (bool, List[str])`).
"""
import re
from typing import List, Tuple

_INJECTION_PATTERNS = [
    r"ignore (all|any|the) (previous|prior|above) (instructions|prompts?)",
    r"disregard (all|any|the) (previous|prior|above)",
    r"you are now (in )?(dan|developer|jailbreak) mode",
    r"pretend (you|to) (are|be) .* (with no|without) (restrictions|filters|rules)",
    r"reveal (your|the) (system prompt|instructions)",
    r"act as (if you (are|were)|an unrestricted)",
    r"forget (everything|all) (you (were|have been) told|previous instructions)",
    r"bypass (the )?(safety|governance|content) (filters?|guardrails?|policy)",
    r"\bDAN\b.*(prompt|mode)",
    r"repeat (the )?(system|hidden) prompt",
    r"what (is|are) your (system prompt|instructions|initial prompt)",
    r"override (your|the) (rules|guidelines|configuration)",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def detect(text: str) -> Tuple[bool, List[str]]:
    """Returns (is_injection, matched_patterns)."""
    matches = [p.pattern for p in _COMPILED if p.search(text)]
    return (len(matches) > 0, matches)


def injection_risk_contribution(text: str) -> int:
    """Points added to the overall AI Risk Score (0-100 scale) if injection detected."""
    is_injection, matches = detect(text)
    if not is_injection:
        return 0
    return min(40 + 5 * len(matches), 60)
