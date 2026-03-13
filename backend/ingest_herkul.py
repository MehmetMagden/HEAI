import os, sys, json, hashlib
from pathlib import Path
import torch
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH    = os.path.join(BASE_DIR, "data", "chroma_db")
BAMTELI_DIR    = os.path.join(BASE_DIR, "data", "bamteli")
PROCESSED_FILE = os.path.join(BASE_DIR, "data", "processed_bamteli.json")
COLLECTION     = "hocaefendi_books"
CHUNK_SIZE     = 500
CHUNK_OVERLAP  = 50
BATCH_SIZE     = 100

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Cihaz: {device.upper()}")
model = SentenceTransformer("intfloat/multilingual-e5-large", device=device)
print("Model yuklendi.")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(
    name=COLLECTION,
    metadata={"hnsw:space": "cosine"}
)
print(f"Koleksiyon: {COLLECTION} | Mevcut parca: {collection.count()}")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " "]
)

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_processed(data):
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def file_hash(fp):
    with open(fp, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def parse_file(fp):
    with open(fp, encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    title, source, text_lines, in_content = "", "", [], False
    for line in lines:
        if line.startswith("BASLIK:") or line.startswith("BAŞLIK:"):
            title = line.split(":", 1)[1].strip()
        elif line.startswith("KAYNAK:"):
            source = line.replace("KAYNAK:", "").strip()
        elif "=" * 20 in line:
            in_content = True
        elif in_content:
            text_lines.append(line)
    return title, source, "\n".join(text_lines).strip()

def embed(texts):
    prefixed = ["passage: " + t for t in texts]
    vecs = model.encode(prefixed, normalize_embeddings=True, show_progress_bar=False)
    return vecs.tolist()

def main():
    if not os.path.exists(BAMTELI_DIR):
        print(f"HATA: {BAMTELI_DIR} bulunamadi!")
        sys.exit(1)

    txt_files = list(Path(BAMTELI_DIR).glob("*.txt"))
    print(f"{len(txt_files)} Bamteli dosyasi bulundu.")

    processed = load_processed()
    total_new = 0
    file_count = 0

    for fp in txt_files:
        fname = fp.name
        fhash = file_hash(fp)
        if fname in processed and processed[fname] == fhash:
            continue
        title, source, text = parse_file(fp)
        if len(text) < 200:
            continue
        chunks = splitter.split_text(text)
        documents, metadatas, ids = [], [], []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:
                continue
            doc_id = f"bamteli_{fname}_{i}"
            documents.append(chunk)
            metadatas.append({
                "source": title or fname,
                "source_type": "bamteli",
                "url": source,
                "chunk_id": i
            })
            ids.append(doc_id)
        if documents:
            for i in range(0, len(documents), BATCH_SIZE):
                batch_docs = documents[i:i+BATCH_SIZE]
                batch_meta = metadatas[i:i+BATCH_SIZE]
                batch_ids  = ids[i:i+BATCH_SIZE]
                batch_embs = embed(batch_docs)
                collection.add(
                    embeddings=batch_embs,
                    documents=["passage: " + d for d in batch_docs],
                    metadatas=batch_meta,
                    ids=batch_ids
                )
            total_new += len(documents)
            file_count += 1
            if file_count % 50 == 0:
                print(f"  {file_count} dosya islendi, {total_new} parca eklendi...")
        processed[fname] = fhash

    save_processed(processed)

    if total_new > 0:
        print(f"\nTamamlandi! {total_new} yeni parca eklendi.")
        print(f"Koleksiyon toplam: {collection.count()} parca")
    else:
        print("Yeni eklenecek icerik yok.")

if __name__ == "__main__":
    main()