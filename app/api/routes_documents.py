"""
/documents — upload and ingest company policies/SOPs into the RAG pipeline.
"""
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import Document
from app.rag.ingestion import ingest_file

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form("policy"),
    db: Session = Depends(get_db),
):
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        doc_id, chunk_count = ingest_file(tmp_path, filename, source_type)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    record = Document(
        id=doc_id,
        filename=filename,
        source_type=source_type,
        chunk_count=chunk_count,
        status="processed" if chunk_count > 0 else "failed",
    )
    db.add(record)
    db.commit()

    return {"doc_id": doc_id, "filename": filename, "chunks_indexed": chunk_count}


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "source_type": d.source_type,
            "chunk_count": d.chunk_count,
            "status": d.status,
            "uploaded_at": d.uploaded_at.isoformat(),
        }
        for d in docs
    ]
