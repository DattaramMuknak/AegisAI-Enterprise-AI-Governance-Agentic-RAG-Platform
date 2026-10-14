"""
PII detection & redaction.

Uses Microsoft Presidio when available (spaCy-backed NER + regex recognizers
for emails, phone numbers, SSNs, credit cards, etc). Falls back to a
lightweight regex-only detector so the service still works in environments
where the spaCy model hasn't been downloaded (e.g. minimal containers).
"""
import re
from dataclasses import dataclass
from typing import List, Tuple

_REGEX_PATTERNS = {
    "EMAIL_ADDRESS": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE_NUMBER": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "AADHAAR": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "IP_ADDRESS": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


@dataclass
class PIIFinding:
    entity_type: str
    start: int
    end: int
    text: str


class PIIDetector:
    def __init__(self, use_presidio: bool = True):
        self.engine = None
        if use_presidio:
            try:
                from presidio_analyzer import AnalyzerEngine
                self.engine = AnalyzerEngine()
            except Exception:
                # spaCy model likely not downloaded; fall back silently.
                self.engine = None

    def analyze(self, text: str) -> List[PIIFinding]:
        findings: List[PIIFinding] = []

        if self.engine is not None:
            results = self.engine.analyze(text=text, language="en")
            for r in results:
                findings.append(
                    PIIFinding(
                        entity_type=r.entity_type,
                        start=r.start,
                        end=r.end,
                        text=text[r.start:r.end],
                    )
                )
            return findings

        # Regex fallback
        for entity_type, pattern in _REGEX_PATTERNS.items():
            for m in pattern.finditer(text):
                findings.append(
                    PIIFinding(entity_type=entity_type, start=m.start(), end=m.end(), text=m.group())
                )
        return findings

    def redact(self, text: str) -> Tuple[str, List[PIIFinding]]:
        """Returns (redacted_text, findings). Redaction is done right-to-left
        so earlier offsets stay valid while we mutate the string."""
        findings = self.analyze(text)
        findings_sorted = sorted(findings, key=lambda f: f.start, reverse=True)

        redacted = text
        for f in findings_sorted:
            placeholder = f"[REDACTED_{f.entity_type}]"
            redacted = redacted[: f.start] + placeholder + redacted[f.end:]

        return redacted, findings


pii_detector = PIIDetector()
