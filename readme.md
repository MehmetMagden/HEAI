# 🕌 HocaefendiAI

Türkçe konuşan, İslami ilim geleneğinden beslenen yapay zeka asistanı.
Kullanıcıların sorularına hikmet, tevazu ve irfanla cevap verir.

---

## 🛠️ Teknoloji Yığını

| Katman     | Teknoloji                        |
|------------|----------------------------------|
| LLM        | Qwen2.5 7B (Ollama)              |
| RAG        | ChromaDB + multilingual-e5-large |
| Backend    | Python / FastAPI                 |
| TTS        | Coqui XTTS v2                    |
| STT        | OpenAI Whisper                   |
| Frontend   | Flutter / Dart                   |
| Auth       | Google OAuth 2.0                 |
| Deploy     | Cloudflare Tunnel                |

---

## 📋 Gereksinimler

- Python 3.10+
- Ollama
- NVIDIA GPU (önerilen: RTX 3060 12GB+)
- Flutter SDK

---

## 🚀 Kurulum

```bash
# 1. Repo'yu klonla
git clone https://github.com/MehmetMagden/HEAI.git
cd HEAI

# 2. Sanal ortam oluştur
python -m venv venv
venv\Scripts\activate        # Windows

# 3. Bağımlılıkları yükle
pip install -r backend/requirements.txt

# 4. Ollama modellerini çek
ollama pull qwen2.5:7b-instruct-q5_K_M

# 5. .env dosyasını oluştur
copy backend\.env.example backend\.env

# 6. Sunucuyu başlat
cd backend
uvicorn main:app --reload