"""
Document ingestion: extract text from uploaded policy/SOP files, chunk it,
and hand chunks off to the vector store for embedding + upsert.
"""
import uuid
from pathlib import Path
from typing import Tuple

from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.rag.vector_store import upsert_documents

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".docx":
        doc = DocxDocument(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    if ext in (".txt", ".md"):
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")

    raise ValueError(f"Unsupported file type: {ext}")


def ingest_file(file_path: str, filename: str, source_type: str = "policy") -> Tuple[str, int]:
    """
    Full pipeline: extract -> chunk -> embed -> upsert.
    Returns (doc_id, chunk_count).
    """
    doc_id = str(uuid.uuid4())
    text = extract_text(file_path)

    if not text.strip():
        return doc_id, 0

    chunks = _splitter.split_text(text)
    metadatas = [
        {"doc_id": doc_id, "filename": filename, "source_type": source_type, "chunk_index": i}
        for i in range(len(chunks))
    ]

    upsert_documents(chunks, metadatas)
    return doc_id, len(chunks)
