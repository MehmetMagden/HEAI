# services/rag_service.py
import os
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
import chromadb
import torch

# ── Yollar ──────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db")
PDF_DIR     = os.path.join(BASE_DIR, "data", "pdfs")

# ── Türkçe Embedding Modeli ──────────────────────────────────
print("📦 Embedding modeli yükleniyor...")
# _embed_model = SentenceTransformer("intfloat/multilingual-e5-large")  # Sadece CPU kullanmak için, tavsiye etmem, pdf leri yüklemek 10 saat sürdü

_device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️  Embedding cihazı: {_device.upper()}")
_embed_model = SentenceTransformer("intfloat/multilingual-e5-large", device=_device)

print("✅ Embedding modeli hazır.")


class TurkishEmbeddingFunction:
    """ChromaDB için özel Türkçe embedding fonksiyonu."""

    def name(self) -> str:
        return "turkish_embedding_function"

    def __call__(self, input: list[str]) -> list[list[float]]:
        prefixed = ["passage: " + text for text in input]
        embeddings = _embed_model.encode(prefixed, normalize_embeddings=True)
        return embeddings.tolist()


_embedding_fn = TurkishEmbeddingFunction()


def get_vectorstore():
    """ChromaDB bağlantısını döndür."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name="hocaefendi_books",
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF'den metin çıkar."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def ingest_pdf(pdf_path: str) -> int:
    """Tek PDF'yi ChromaDB'ye ekle."""
    collection = get_vectorstore()   # ← Kendi collection'ını alıyor
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    text = extract_text_from_pdf(pdf_path)

    if len(text.strip()) < 100:
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(text)

    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 50:
            continue
        doc_id = f"{book_name}_{i}"
        documents.append("passage: " + chunk)
        metadatas.append({"source": book_name, "chunk_id": i})
        ids.append(doc_id)

    if documents:
        # Büyük kitaplar için batch'ler halinde ekle (bellek taşmasın)
        batch_size = 500
        for i in range(0, len(documents), batch_size):
            collection.add(
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )

    return len(documents)


def retrieve_context(query: str, k: int = 4) -> str:

    if len(query.strip().split()) <= 3:
        return ""

    collection = get_vectorstore()

    query_embedding = _embed_model.encode(
        ["query: " + query],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )

    if not results["documents"] or not results["documents"][0]:
        print("⚠️ RAG: Hiç sonuç bulunamadı!")
        return ""

    # ── DEBUG: Mesafeleri göster ──────────────────────────────
    print(f"🔍 RAG sorgu: '{query[:50]}'")
    for i, (meta, dist) in enumerate(zip(
        results["metadatas"][0],
        results["distances"][0]
    )):
        status = "✅" if dist <= 0.5 else "❌ FİLTRELENDİ"
        print(f"  [{i+1}] dist={dist:.4f} {status} → {meta.get('source','?')[:40]}")
    # ─────────────────────────────────────────────────────────

    context_parts = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        if dist > 0.7:
            continue
        source = meta.get("source", "Bilinmeyen Kaynak")
        clean_doc = doc.replace("passage: ", "", 1)
        context_parts.append(f"[{source}]\n{clean_doc}")

    return "\n\n---\n\n".join(context_parts)

def get_stats() -> dict:
    """ChromaDB istatistiklerini döndür."""
    collection = get_vectorstore()
    return {"total_chunks": collection.count()}