# services/llm_service.py
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q5_K_M")
OLLAMA_NUM_CTX  = int(os.getenv("OLLAMA_NUM_CTX", "32768"))


async def chat(messages: list[dict], stream: bool = False) -> str:
    """
    Ollama ile sohbet et.
    messages: [{"role": "system/user/assistant", "content": "..."}]
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
        "options": {
            "num_ctx": OLLAMA_NUM_CTX,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


async def chat_stream(messages: list[dict]):
    """
    Streaming yanıt üret — kelime kelime gelir (daha iyi UX).
    Generator olarak kullanılır.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
        "options": {
            "num_ctx": OLLAMA_NUM_CTX,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if not data.get("done", False):
                        token = data.get("message", {}).get("content", "")
                        if token:
                            yield token


async def detect_emotion(text: str) -> str:
    """Metinden duygu tonu çıkar."""
    from prompts.hocaefendi_prompt import EMOTION_PROMPT

    messages = [
        {
            "role": "user",
            "content": EMOTION_PROMPT.format(text=text[:500])
        }
    ]

    result = await chat(messages)
    emotion = result.strip().lower()

    valid = ["neutral", "thoughtful", "joyful", "serious", "compassionate", "sorrowful"]
    return emotion if emotion in valid else "neutral"