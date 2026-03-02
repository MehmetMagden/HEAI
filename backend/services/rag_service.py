# services/rag_service.py
import os
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED    = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHROMA_PATH     = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")


def get_vectorstore():
    """ChromaDB bağlantısını döndür."""
    embeddings = OllamaEmbeddings(
        model=OLLAMA_EMBED,
        base_url=OLLAMA_BASE_URL
    )
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
        collection_name="hocaefendi"
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF'den metin çıkar (PyMuPDF ile)."""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text


def ingest_pdf(pdf_path: str, book_title: str, author: str = "Fethullah Gülen") -> int:
    """PDF'i işle ve ChromaDB'ye ekle. Döndürür: chunk sayısı"""
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.create_documents(
        texts=[raw_text],
        metadatas=[{
            "book": book_title,
            "author": author,
            "source": os.path.basename(pdf_path),
            "type": "kitap"
        }]
    )

    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    return len(chunks)


def retrieve_context(query: str, k: int = 4) -> str:
    """Soruya en alakalı kitap parçalarını getir."""
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=k)
    if not docs:
        return ""

    context_parts = []
    for doc in docs:
        book = doc.metadata.get("book", "Bilinmeyen Kitap")
        context_parts.append(f"[{book}]\n{doc.page_content}")

    return "\n\n---\n\n".join(context_parts)


def get_stats() -> dict:
    """Veritabanı istatistiklerini döndür."""
    vectorstore = get_vectorstore()
    count = vectorstore._collection.count()
    return {"total_chunks": count}