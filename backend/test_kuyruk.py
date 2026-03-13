import asyncio
import httpx

async def sor(idx):
    async with httpx.AsyncClient(timeout=120) as client:
        print(f"Kullanıcı {idx} soru gönderdi")
        async with client.stream("POST", "http://127.0.0.1:8000/chat/stream",
            json={"message": "tevekkül nedir", "history": [], "use_rag": True, "top_k": 5}
        ) as r:
            async for chunk in r.aiter_text():
                if "[QUEUE]" in chunk:
                    print(f"Kullanıcı {idx} → KUYRUK: {chunk}")
                elif "[QUEUE_START]" in chunk:
                    print(f"Kullanıcı {idx} → Sıra geldi!")
                elif chunk.strip():
                    print(f"Kullanıcı {idx} → {chunk[:50]}")

async def main():
    await asyncio.gather(sor(1), sor(2), sor(3))

asyncio.run(main())