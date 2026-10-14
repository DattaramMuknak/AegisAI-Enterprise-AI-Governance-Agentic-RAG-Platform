"""
Toxicity / safety scoring.

Lightweight lexicon + heuristic scorer by default (zero external
dependencies, deterministic, fast — good for an audit trail). Swap
`score()` for a call to a hosted moderation API/model if higher recall
is needed; the rest of the governance layer only depends on the
(0.0-1.0) float this returns.
"""

_TOXIC_TERMS = [
    "kill you", "hate speech", "slur", "attack them", "bomb making",
    "self harm", "suicide method", "racial slur", "explicit violence",
]

_SEVERITY_WEIGHT = 0.3


def score(text: str) -> float:
    """Returns a toxicity score between 0.0 (safe) and 1.0 (highly toxic)."""
    text_lower = text.lower()
    hits = sum(1 for term in _TOXIC_TERMS if term in text_lower)

    # Additional heuristic: excessive caps + exclamation as aggression proxy
    aggression_signal = 0.0
    if len(text) > 20:
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.5 and "!" in text:
            aggression_signal = 0.15

    raw_score = min(hits * _SEVERITY_WEIGHT, 1.0) + aggression_signal
    return round(min(raw_score, 1.0), 3)


def is_blocked(text: str, threshold: float) -> bool:
    return score(text) >= threshold
