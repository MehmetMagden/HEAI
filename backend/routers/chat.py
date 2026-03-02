# routers/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prompts.hocaefendi_prompt import SYSTEM_PROMPT
from services import llm_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    stream: bool = False


class ChatResponse(BaseModel):
    text: str
    emotion: str


def build_messages(user_message: str, history: list[dict], context: str = "") -> list[dict]:
    """Sistem promptu + geçmiş + yeni mesajı birleştir."""
    system_content = SYSTEM_PROMPT.format(
        context=f"\n## KİTAPLARDAN ALINTLAR\n{context}" if context else ""
    )

    messages = [{"role": "system", "content": system_content}]
    messages.extend(history[-10:])  # Son 10 mesajı al (context taşmasın)
    messages.append({"role": "user", "content": user_message})

    return messages


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Normal (tek seferde) yanıt."""
    messages = build_messages(request.message, request.history)
    response_text = await llm_service.chat(messages)
    emotion = await llm_service.detect_emotion(response_text)

    return ChatResponse(text=response_text, emotion=emotion)


@router.post("/stream")
async def stream_message(request: ChatRequest):
    """Streaming yanıt — kelime kelime gelir."""
    messages = build_messages(request.message, request.history)

    async def generate():
        async for token in llm_service.chat_stream(messages):
            yield token

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/health")
async def health():
    """Servis sağlık kontrolü."""
    return {"status": "ok", "model": llm_service.OLLAMA_MODEL}