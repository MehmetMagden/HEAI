# 🕌 HocaefendiAI

Fethullah Gülen'in kitap ve sohbetlerinden beslenen, onun kimliğine bürünen
Türkçe yapay zeka asistanı.

## 🛠️ Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| LLM | Qwen2.5 7B (Ollama) |
| RAG | LangChain + ChromaDB |
| Backend | Python / FastAPI |
| TTS | Coqui XTTS v2 |
| STT | OpenAI Whisper |
| Frontend | Flutter / Dart |
| Auth | Google OAuth 2.0 |
| Deploy | Google Cloud Run |

## 🚀 Kurulum

### Gereksinimler
- Python 3.10+
- [Ollama](https://ollama.com)
- NVIDIA GPU (önerilen: RTX 3060 12GB+)

### Adımlar

```bash
# 1. Repo'yu klonla
git clone https://github.com/KULLANICI_ADIN/hocaefendi-ai.git
cd hocaefendi-ai

# 2. Sanal ortam
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Kütüphaneler
pip install -r backend/requirements.txt

# 4. Ollama modelleri
ollama pull qwen2.5:7b-instruct-q5_K_M
ollama pull nomic-embed-text

# 5. .env dosyasını oluştur (.env.example'dan kopyala)
copy backend\.env.example backend\.env

# 6. Sunucuyu başlat
cd backend
uvicorn main:app --reload