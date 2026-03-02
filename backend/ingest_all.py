# ingest_all.py — 83 kitabı ChromaDB'ye yükle
import os
import sys
import time

# Path ayarı
sys.path.insert(0, os.path.dirname(__file__))

from services.rag_service import ingest_pdf, get_stats

PDF_DIR = os.path.join(os.path.dirname(__file__), "data", "pdfs")


def clean_title(filename: str) -> str:
    """Dosya adından kitap başlığı çıkar."""
    title = filename.replace(".pdf", "")
    title = title.replace("_", " ").replace("-", " ")
    # Baştaki/sondaki boşlukları temizle
    return title.strip()


def ingest_all():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        print("❌ data/pdfs/ klasöründe PDF bulunamadı!")
        return

    total = len(pdf_files)
    print(f"{'='*55}")
    print(f"  HocaefendiAI — Toplu Kitap Yükleme")
    print(f"  {total} kitap bulundu")
    print(f"{'='*55}\n")

    # Başlangıç istatistiği
    stats_before = get_stats()
    print(f"📊 Mevcut chunk sayısı: {stats_before['total_chunks']}\n")

    success = 0
    failed  = 0
    total_chunks = 0
    start_time = time.time()

    for i, filename in enumerate(sorted(pdf_files), 1):
        pdf_path    = os.path.join(PDF_DIR, filename)
        book_title  = clean_title(filename)
        file_size   = os.path.getsize(pdf_path) / 1024  # KB

        print(f"[{i:02d}/{total}] 📖 {book_title[:50]}")
        print(f"         Boyut: {file_size:.0f} KB")

        try:
            t = time.time()
            chunks = ingest_pdf(pdf_path, book_title)
            elapsed = time.time() - t

            if chunks > 0:
                print(f"         ✅ {chunks} chunk — {elapsed:.1f}s")
                success += 1
                total_chunks += chunks
            else:
                print(f"         ⚠️  Metin çıkarılamadı (taranmış PDF olabilir)")
                failed += 1

        except Exception as e:
            print(f"         ❌ Hata: {e}")
            failed += 1

        # İlerleme çubuğu
        pct = int((i / total) * 30)
        bar = "█" * pct + "░" * (30 - pct)
        print(f"         [{bar}] %{i*100//total}\n")

    # Özet
    elapsed_total = time.time() - start_time
    stats_after = get_stats()

    print(f"\n{'='*55}")
    print(f"  ✅ TAMAMLANDI!")
    print(f"{'='*55}")
    print(f"  Başarılı  : {success} kitap")
    print(f"  Başarısız : {failed} kitap")
    print(f"  Yeni chunk: {total_chunks:,}")
    print(f"  Toplam DB : {stats_after['total_chunks']:,} chunk")
    print(f"  Süre      : {elapsed_total/60:.1f} dakika")
    print(f"{'='*55}")


if __name__ == "__main__":
    ingest_all()