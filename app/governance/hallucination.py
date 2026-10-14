"""
Hallucination / evidence-grounding validation.

Approach: lexical-overlap grounding score between the generated answer and
the retrieved context (cheap, explainable, no extra LLM call). This is the
same family of technique used by many production RAG evaluators as a fast
first-pass check, with an LLM-as-judge escalation path for borderline cases.
"""
import re
from typing import List

_STOPWORDS = set(
    "a an the is are was were be been being of to in on at for with and or "
    "this that these those it its as by from into over under not no do "
    "does did have has had will would can could should may might".split()
)


def _tokenize(text: str) -> set:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def grounding_score(answer: str, retrieved_chunks: List[str]) -> float:
    """
    Returns a 0.0-1.0 score estimating how well the answer is supported
    by the retrieved evidence. Computed as the fraction of meaningful
    answer tokens that also appear somewhere in the retrieved context.
    """
    if not answer.strip():
        return 0.0
    if not retrieved_chunks:
        return 0.0

    answer_tokens = _tokenize(answer)
    if not answer_tokens:
        return 1.0  # nothing substantive to hallucinate about

    context_tokens = set()
    for chunk in retrieved_chunks:
        context_tokens |= _tokenize(chunk)

    if not context_tokens:
        return 0.0

    overlap = answer_tokens & context_tokens
    return round(len(overlap) / len(answer_tokens), 3)


def is_hallucination(answer: str, retrieved_chunks: List[str], min_score: float) -> bool:
    return grounding_score(answer, retrieved_chunks) < min_score


def confidence_label(grounding: float, risk_score: int) -> str:
    if grounding >= 0.75 and risk_score < 30:
        return "High"
    if grounding >= 0.5 and risk_score < 60:
        return "Medium"
    return "Low"
