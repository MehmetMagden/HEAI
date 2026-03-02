# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat

app = FastAPI(
    title="HocaefendiAI API",
    description="Fethullah Gülen AI Asistanı",
    version="1.0.0"
)

# CORS — Flutter web için gerekli
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları bağla
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


@app.get("/")
async def root():
    return {
        "app": "HocaefendiAI",
        "version": "1.0.0",
        "status": "çalışıyor ✅"
    }