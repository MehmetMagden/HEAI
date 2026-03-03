# routers/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prompts.hocaefendi_prompt import SYSTEM_PROMPT
from services import llm_service, rag_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    use_rag: bool = True
    stream: bool = False


class ChatResponse(BaseModel):
    text: str
    emotion: str
    sources: list[str] = []


def build_messages(user_message: str, history: list[dict], context: str = "") -> list[dict]:
    """Sistem promptu + geçmiş + yeni mesajı birleştir."""

    # Sohbet geçmişini düz metin olarak hazırla
    chat_history_text = ""
    if history:
        lines = []
        for msg in history[-10:]:
            role = "Siz" if msg.get("role") == "user" else "Hocaefendi"
            lines.append(f"{role}: {msg.get('content', '')}")
        chat_history_text = "\n".join(lines)

    # Prompt'taki {context} ve {chat_history} yerlerine koy
    system_content = SYSTEM_PROMPT.replace(
        "{context}", context if context else "(Bağlam bilgisi mevcut değil.)"
    ).replace(
        "{chat_history}", chat_history_text if chat_history_text else "(Henüz sohbet geçmişi yok.)"
    )

    messages = [{"role": "system", "content": system_content}]
    messages.append({"role": "user", "content": user_message})

    return messages


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Normal (tek seferde) yanıt."""

    # 1. RAG: İlgili kitap parçalarını getir
    context = ""
    sources = []
    if request.use_rag:
        context = rag_service.retrieve_context(request.message)
        if context:
            import re
            sources = list(set(re.findall(r'\[(.+?)\]', context)))

    # 2. Mesajları oluştur ve LLM'e gönder
    messages = build_messages(request.message, request.history, context)
    response_text = await llm_service.chat(messages)

    # 3. Duygu analizi
    emotion = await llm_service.detect_emotion(response_text)

    return ChatResponse(text=response_text, emotion=emotion, sources=sources)


@router.post("/stream")
async def stream_message(request: ChatRequest):
    """Streaming yanıt — kelime kelime gelir."""
    context = ""
    if request.use_rag:
        context = rag_service.retrieve_context(request.message)

    messages = build_messages(request.message, request.history, context)

    async def generate():
        async for token in llm_service.chat_stream(messages):
            yield token

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/health")
async def health():
    return {"status": "ok", "model": llm_service.OLLAMA_MODEL}