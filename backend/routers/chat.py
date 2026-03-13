from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from prompts.hocaefendi_prompt import SYSTEM_PROMPT
from services import llm_service, rag_service
from services.emotion_service import detect_emotion
from core.limiter import limiter
import re


def post_process(text: str) -> str:
    # 1. Uydurma ayet/hadis numaralarını temizle
    text = re.sub(r'\b\d{1,3}:\d{1,3}\b', '', text)
    text = re.sub(r'\([^)]*\d{1,3}[:/]\d{1,3}[^)]*\)', '', text)
    text = re.sub(r'[Ss]ûr[ae][a-zA-ZğüşıöçĞÜŞİÖÇ\s]+,?\s*\d+', '', text)

    # 2. Liste işaretlerini kaldır
    text = re.sub(r'^\s*[-•*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+[.)]\s+', '', text, flags=re.MULTILINE)

    # 3. Markdown temizle
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)

    # 4. Paragraf sayısını sınırla (max 5) — eski kodda [8] yazıyordu, [:5] olmalı
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) > 5:
        paragraphs = paragraphs[:5]
    text = '\n\n'.join(paragraphs)

    # 5. Fazla boş satırları temizle
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def estimate_tokens(message: str) -> int:
    msg = message.lower().strip()

    greetings = ['nasılsınız', 'merhaba', 'selamün', 'esselam',
                 'iyi misiniz', 'ne haber', 'hayırlı']
    if any(g in msg for g in greetings) and len(msg) < 60:
        return 150

    short_q = ['ne demek', 'nedir', 'kimdir', 'ne zaman',
               'kaç', 'hangi', 'kısaca', 'özetle']
    if any(q in msg for q in short_q):
        return 220

    deep_q = ['neden', 'nasıl', 'açıklar mısınız', 'felsefi',
              'hakikat', 'mana', 'hikmet', 'tefekkür',
              'anlat', 'anlayamıyorum', 'ızdırap', 'sıkıntı']
    if any(d in msg for d in deep_q):
        return 500

    return 320


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    use_rag: bool = True
    stream: bool = False
    top_k: int = 15


class ChatResponse(BaseModel):
    text: str
    emotion: str
    sources: list[str] = []


def build_messages(user_message: str, history: list[dict], context: str = "", emotion: str = "tefekkür") -> list[dict]:
    chat_history_text = ""
    if history:
        lines = []
        for msg in history[-10:]:
            role = "Siz" if msg.get("role") == "user" else "Hocaefendi"
            lines.append(f"{role}: {msg.get('content', '')}")
        chat_history_text = "\n".join(lines)

    system_content = SYSTEM_PROMPT.replace(
        "{context}", context if context else "(Bağlam bilgisi mevcut değil.)"
    ).replace(
        "{chat_history}", chat_history_text if chat_history_text else "(Henüz sohbet geçmişi yok.)"
    ).replace(
        "{emotion}", emotion
    ).replace(
        "{telif}", emotion
    )

    messages = [{"role": "system", "content": system_content}]
    messages.append({"role": "user", "content": user_message})
    return messages


@router.post("/message", response_model=ChatResponse)
@limiter.limit("10/minute")
async def send_message(request: Request, body: ChatRequest):
    context = ""
    sources = []
    if body.use_rag:
        context = rag_service.retrieve_context(body.message, k=body.top_k)
        print(f"📚 Context uzunluğu: {len(context)} karakter")
        print(f"📚 Context önizleme: {context[:150]}")
        if context:
            found_sources = re.findall(r'$(.+?)$', context)
            if found_sources:
                sources = list(dict.fromkeys(found_sources))
            print(f"📚 Bulunan sources: {sources}")

    input_emotion = detect_emotion(body.message)
    messages = build_messages(body.message, body.history, context, input_emotion)
    response_text = await llm_service.chat(messages)

    output_emotion = detect_emotion(response_text)
    cleaned_response_text = post_process(
        re.sub(r'\s*$.*?$\s*', '', response_text).strip()
    )

    return ChatResponse(text=cleaned_response_text, emotion=output_emotion, sources=sources)


@router.post("/stream")
@limiter.limit("10/minute")
async def stream_message(request: Request, body: ChatRequest):
    input_emotion = detect_emotion(body.message)
    context = ""
    sources = []
    if body.use_rag:
        context = rag_service.retrieve_context(body.message, k=body.top_k)
        if context:
            found_sources = re.findall(r'$(.+?)$', context)
            if found_sources:
                sources = list(dict.fromkeys(found_sources))

    messages = build_messages(body.message, body.history, context, input_emotion)

    # Soru tipine göre token bütçesi
    max_tokens = estimate_tokens(body.message)

    async def generate():
        import json
        source_details = []
        if context:
            parts = context.split("\n\n---\n\n")
            for part in parts:
                lines = part.strip().split("\n", 1)
                if lines and lines[0].startswith("[") and lines[0].endswith("]"):
                    name = lines[0][1:-1]
                    content = lines[1].strip() if len(lines) > 1 else ""
                    source_details.append({
                        "name": name,
                        "content": content[:500]
                    })
        yield f"[SOURCES]{json.dumps(source_details, ensure_ascii=False)}[/SOURCES]"
        async for token in llm_service.chat_stream(messages, max_tokens=max_tokens):
            yield token

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/health")
async def health():
    return {"status": "ok", "model": llm_service.OLLAMA_MODEL}