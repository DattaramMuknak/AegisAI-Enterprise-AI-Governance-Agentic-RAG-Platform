"""
Response Agent — calls the LLM (Groq) with the sanitized prompt and
retrieved evidence to produce the final grounded answer.
"""
from typing import List

from app.llm.groq_client import generate_answer


def run(question: str, context_chunks: List[str]) -> dict:
    return generate_answer(question, context_chunks)
