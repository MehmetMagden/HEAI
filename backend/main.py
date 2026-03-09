# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, rag
from routers.voice import router as voice_router
from routers.emotion import router as emotion_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(
    title="HocaefendiAI API",
    description="Fethullah Gülen AI Asistanı",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(rag.router,  prefix="/rag",  tags=["RAG"])
app.include_router(voice_router)
app.include_router(emotion_router)

@app.get("/")
async def root():
    return {"app": "HocaefendiAI", "version": "1.0.0", "status": "çalışıyor ✅"}


# ... mevcut router'lar ...

# Flutter web dosyalarını serve et
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
if os.path.exists(WEB_DIR):
    app.mount("/app", StaticFiles(directory=WEB_DIR, html=True), name="web")

@app.get("/")
async def root():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok"}    