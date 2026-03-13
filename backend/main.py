from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import chat, rag
from routers.voice import router as voice_router
from routers.emotion import router as emotion_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.limiter import limiter   # ← artık buradan geliyor
import os
from starlette.responses import Response

app = FastAPI(title="HocaefendiAI API")

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

@app.get("/health")
async def health():
    return {"status": "ok", "model": "qwen2.5:7b-instruct-q5_K_M"}

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

@app.get("/")
async def root():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"app": "HocaefendiAI", "status": "çalışıyor ✅"}

if os.path.exists(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    if "WinError 123" in str(exc) or "OSError" in str(exc):
        return Response(status_code=404, content="Not Found")
    raise exc
