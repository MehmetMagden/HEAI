import os
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.voice_service import voice_service
from services.llm_service import chat
from services.rag_service import retrieve_context
from prompts.hocaefendi_prompt import SYSTEM_PROMPT

from fastapi.responses import StreamingResponse as FastAPIStreaming
import asyncio
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "audio_output"
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "audio_upload"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class SynthesizeRequest(BaseModel):
    text: str
    filename: str = "output.wav"


# ── STT: Ses → Metin ─────────────────────────────────────
@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Yüklenen ses dosyasını Türkçe metne çevirir."""
    try:
        file_id = str(uuid.uuid4())[:8]
        upload_path = str(UPLOAD_DIR / f"{file_id}_{file.filename}")

        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)

        text = voice_service.transcribe(upload_path)
        os.remove(upload_path)

        return {"success": True, "text": text}

    except Exception as e:
        logger.error(f"Transkripsiyon hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── TTS: Metin → Ses ─────────────────────────────────────
@router.post("/synthesize")
async def synthesize_text(request: SynthesizeRequest):
    """Metni Türkçe sese çevirir, WAV dosyası döner."""
    try:
        file_id = str(uuid.uuid4())[:8]
        filename = f"{file_id}_{request.filename}"

        output_path = voice_service.synthesize(request.text, filename)

        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=filename
        )

    except Exception as e:
        logger.error(f"Sentez hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Tam Ses Sohbet: Ses → Metin → LLM → Ses ─────────────
@router.post("/chat")
async def voice_chat(
    file: UploadFile = File(...),
    use_rag: bool = True
):
    """
    Tam ses sohbet pipeline:
    1. Ses → Metin (Whisper)
    2. Metin → LLM yanıtı (Qwen2.5 + RAG)
    3. LLM yanıtı → Ses (XTTS v2)
    """
    try:
        # 1. STT
        file_id = str(uuid.uuid4())[:8]
        upload_path = str(UPLOAD_DIR / f"{file_id}_{file.filename}")

        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)

        user_text = voice_service.transcribe(upload_path)
        os.remove(upload_path)
        logger.info(f"🎙️ Kullanıcı dedi: {user_text}")

        # 2. RAG + LLM
        context = ""
        if use_rag:
            results = retrieve_context(user_text)
            if results:
                context = "\n\n".join([r["text"] for r in results[:3]])

        # Mesajları oluştur
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            user_content = f"[İLGİLİ BAĞLAM]\n{context}\n\n[SORU]\n{user_text}"
        else:
            user_content = user_text
        messages.append({"role": "user", "content": user_content})

        ai_response = await chat(messages)
        logger.info(f"🤖 AI yanıtı: {ai_response[:80]}...")

        # 3. TTS
        output_filename = f"{file_id}_response.wav"
        output_path = voice_service.synthesize(ai_response, output_filename)

        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=output_filename,
            headers={
                "X-User-Text": user_text[:200],
                "X-AI-Response": ai_response[:200]
            }
        )

    except Exception as e:
        logger.error(f"Ses sohbet hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))




class StreamTTSRequest(BaseModel):
    text: str
    session_id: str = ""

@router.post("/synthesize-stream")
async def synthesize_stream(request: StreamTTSRequest):
    """
    Metni cümlelere böl, her cümleyi ayrı sentezle.
    Her cümle hazır olunca SSE ile URL gönder.
    """
    session_id = request.session_id or str(uuid.uuid4())[:8]
    sentences = voice_service.split_into_sentences(request.text)

    async def generate():
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            try:
                filename = f"sentence_{session_id}_{i}.wav"
                output_path = voice_service.synthesize_sentence(sentence, filename)

                if output_path:
                    url = f"/voice/audio/{filename}"
                    data = json.dumps({
                        "index": i,
                        "total": len(sentences),
                        "url": url,
                        "text": sentence
                    }, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                    # Flutter'ın indirip çalmaya başlaması için küçük bekleme
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Cümle {i} sentez hatası: {e}")
                continue

        # Tüm cümleler bitti sinyali
        yield f"data: {json.dumps({'done': True})}\n\n"

        # Eski dosyaları temizle
        voice_service.cleanup_old_audio(max_files=100)

    return FastAPIStreaming(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """Ses dosyasını döndür."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Ses dosyası bulunamadı")
    return FileResponse(
        path=str(file_path),
        media_type="audio/wav",
        filename=filename
    )        



# ── Streaming TTS ─────────────────────────────────────
from pydantic import BaseModel as _BaseModel


class StreamTTSRequest(_BaseModel):
    text: str
    session_id: str = "default"


@router.post("/synthesize-stream")
async def synthesize_stream(request: StreamTTSRequest):
    """Metni cümle cümle sentezler, SSE ile URL'leri gönderir."""
    import uuid, json
    from fastapi.responses import StreamingResponse as _SR

    sentences = voice_service.split_into_sentences(request.text)

    async def generate():
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            try:
                filename = f"sentence_{request.session_id}_{i}.wav"
                path = voice_service.synthesize_sentence(sentence, filename)
                if path:
                    audio_url = f"/voice/audio/{filename}"
                    data = json.dumps({"url": audio_url, "index": i}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
            except Exception as e:
                logger.error(f"Cümle {i} hatası: {e}")
                continue

        # Bitti sinyali
        yield f"data: {json.dumps({'done': True})}\n\n"
        voice_service.cleanup_old_audio()

    return _SR(generate(), media_type="text/event-stream")


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """Üretilen ses dosyasını döner."""
    audio_path = OUTPUT_DIR / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Ses dosyası bulunamadı")
    return FileResponse(str(audio_path), media_type="audio/wav")

