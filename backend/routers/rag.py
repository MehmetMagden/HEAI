# routers/rag.py
import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services import rag_service

router = APIRouter()

PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    book_title: str = Form(...)
):
    """Tek PDF yükle ve RAG'a ekle."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF kabul edilir")

    save_path = os.path.join(PDF_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    chunk_count = rag_service.ingest_pdf(save_path, book_title)
    return {"message": "✅ Eklendi", "book": book_title, "chunks": chunk_count}


@router.get("/stats")
async def get_stats():
    """Kaç chunk var?"""
    return rag_service.get_stats()


@router.get("/search")
async def search(query: str, k: int = 4):
    """Test: Sorguya göre ilgili parçaları getir."""
    context = rag_service.retrieve_context(query, k=k)
    return {"query": query, "context": context}