"""
Groq LLM client, wrapped through LangChain's ChatGroq so it plugs
directly into LangChain chains/agents elsewhere in the codebase.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.core.config import settings

SYSTEM_PROMPT = (
    "You are a compliance-aware enterprise assistant. Answer ONLY using the "
    "provided evidence context. If the evidence does not contain the answer, "
    "say you don't have enough information rather than guessing. Always be "
    "precise, cite which piece of evidence you used, and never fabricate "
    "policy details."
)


def get_llm(temperature: float = 0.1) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=temperature,
    )


def generate_answer(question: str, context_chunks: list[str]) -> dict:
    """
    Calls Groq with the question + retrieved evidence.
    Returns {"answer": str, "token_usage": {...}}.
    """
    llm = get_llm()
    context_block = "\n\n---\n\n".join(
        f"[Evidence {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)
    ) or "No evidence retrieved."

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Evidence:\n{context_block}\n\n"
                f"Question: {question}\n\n"
                f"Answer using only the evidence above, and reference "
                f"[Evidence N] where relevant."
            )
        ),
    ]

    response = llm.invoke(messages)

    usage = {}
    meta = getattr(response, "response_metadata", {}) or {}
    token_usage = meta.get("token_usage", {})
    if token_usage:
        usage = {
            "prompt_tokens": token_usage.get("prompt_tokens", 0),
            "completion_tokens": token_usage.get("completion_tokens", 0),
            "total_tokens": token_usage.get("total_tokens", 0),
        }

    return {"answer": response.content, "token_usage": usage}
