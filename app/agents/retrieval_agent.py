"""
Retrieval Agent — pulls relevant evidence chunks from Pinecone for a query.
"""
from typing import Any, Dict, List

from app.rag.vector_store import similarity_search


def run(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """Returns retrieved evidence sorted by relevance score."""
    return similarity_search(query, top_k=top_k)
