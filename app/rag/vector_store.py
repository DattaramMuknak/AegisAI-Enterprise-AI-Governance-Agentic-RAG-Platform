"""
Pinecone-backed vector store for the Enterprise RAG layer.

Uses HuggingFace sentence-transformer embeddings locally and
LangChain's Pinecone wrapper for retrieval.
"""

from typing import Any, Dict, List

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings

_embeddings = None
_vector_store = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Create and cache the HuggingFace embedding model.
    """
    global _embeddings

    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )

    return _embeddings


def _ensure_index(pc: Pinecone) -> None:
    """
    Create the Pinecone index if it does not already exist.
    """

    existing_indexes = [
        index["name"]
        for index in pc.list_indexes()
    ]

    if settings.PINECONE_INDEX_NAME not in existing_indexes:
        print(
            f"Creating Pinecone index: "
            f"{settings.PINECONE_INDEX_NAME}"
        )

        pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=settings.EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECONE_REGION,
            ),
        )


def get_vector_store() -> PineconeVectorStore:
    """
    Create and cache the LangChain Pinecone vector store.
    """

    global _vector_store

    if _vector_store is None:

        # Validate Pinecone configuration
        if not settings.PINECONE_API_KEY:
            raise ValueError(
                "PINECONE_API_KEY is not configured. "
                "Check your .env file."
            )

        if not settings.PINECONE_INDEX_NAME:
            raise ValueError(
                "PINECONE_INDEX_NAME is not configured."
            )

        # Create Pinecone client
        pc = Pinecone(
            api_key=settings.PINECONE_API_KEY
        )

        # Make sure index exists
        _ensure_index(pc)

        # Create LangChain Pinecone vector store
        _vector_store = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=get_embeddings(),
            pinecone_api_key=settings.PINECONE_API_KEY,
        )

    return _vector_store


def upsert_documents(
    chunks: List[str],
    metadatas: List[Dict[str, Any]],
) -> int:
    """
    Embed and upsert document chunks into Pinecone.

    Each metadata dictionary should contain values such as:
    doc_id, filename, source_type, etc.
    """

    if len(chunks) != len(metadatas):
        raise ValueError(
            "chunks and metadatas must have the same length."
        )

    if not chunks:
        return 0

    store = get_vector_store()

    documents = [
        Document(
            page_content=chunk,
            metadata=metadata,
        )
        for chunk, metadata in zip(chunks, metadatas, strict=True)
    ]

    store.add_documents(documents)

    return len(documents)


def similarity_search(
    query: str,
    top_k: int = 4,
) -> List[Dict[str, Any]]:
    """
    Search Pinecone for documents similar to the query.

    Returns:

    [
        {
            "doc_id": "...",
            "filename": "...",
            "chunk": "...",
            "score": 0.92
        }
    ]
    """

    if not query.strip():
        return []

    store = get_vector_store()

    results = store.similarity_search_with_score(
        query,
        k=top_k,
    )

    output = []

    for document, score in results:
        output.append(
            {
                "doc_id": document.metadata.get(
                    "doc_id",
                    "unknown",
                ),
                "filename": document.metadata.get(
                    "filename"
                ),
                "chunk": document.page_content,
                "score": float(score),
            }
        )

    return output


def delete_document(doc_id: str) -> None:
    """
    Delete all Pinecone vectors belonging to a document.
    """

    if not doc_id:
        raise ValueError("doc_id is required.")

    store = get_vector_store()

    store.delete(
        filter={
            "doc_id": doc_id
        }
    )


def reset_vector_store_cache() -> None:
    """
    Clear the cached vector store and embeddings.

    Useful during development/testing if configuration changes.
    """

    global _embeddings, _vector_store

    _embeddings = None
    _vector_store = None
