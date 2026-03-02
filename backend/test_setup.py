# test_setup.py — Kurulum doğrulama testi
import sys

print("=" * 50)
print("HocaefendiAI — Kurulum Testi")
print("=" * 50)

# 1. Python versiyonu
print(f"\n✅ Python: {sys.version}")

# 2. Kütüphaneler
libs = [
    "fastapi", "uvicorn", "httpx", "langchain",
    "chromadb", "pymupdf", "sqlalchemy", "pyjwt"
]
print("\n📦 Kütüphane Kontrolü:")
for lib in libs:
    try:
        __import__(lib if lib != "pymupdf" else "fitz")
        print(f"  ✅ {lib}")
    except ImportError:
        print(f"  ❌ {lib} — pip install {lib} çalıştır!")

# 3. Ollama bağlantısı
print("\n🦙 Ollama Bağlantı Testi:")
import httpx
try:
    r = httpx.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    print(f"  ✅ Ollama çalışıyor!")
    print(f"  📋 Yüklü modeller: {models}")
    
    if any("qwen2.5" in m for m in models):
        print("  ✅ Qwen2.5 hazır!")
    else:
        print("  ⚠️  Qwen2.5 bulunamadı — 'ollama pull qwen2.5:7b-instruct-q5_K_M' çalıştır")
        
    if any("nomic" in m for m in models):
        print("  ✅ nomic-embed-text hazır!")
    else:
        print("  ⚠️  nomic-embed-text bulunamadı — 'ollama pull nomic-embed-text' çalıştır")
        
except Exception as e:
    print(f"  ❌ Ollama bağlanamadı: {e}")
    print("  → Ollama'nın çalıştığından emin ol (sistem tepsisinde 🦙 simgesi)")

# 4. GPU kontrolü
print("\n🎮 GPU Kontrolü:")
try:
    import torch
    if torch.cuda.is_available():
        print(f"  ✅ GPU: {torch.cuda.get_device_name(0)}")
        print(f"  ✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("  ⚠️  GPU bulunamadı, CPU kullanılacak")
except ImportError:
    print("  ℹ️  torch kurulu değil (şimdilik sorun değil)")

print("\n" + "=" * 50)
print("Test tamamlandı!")
print("=" * 50)