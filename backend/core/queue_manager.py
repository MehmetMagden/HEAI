import asyncio
import time
from typing import Dict

class QueueManager:
    def __init__(self, max_concurrent: int = 1):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue: asyncio.Queue = asyncio.Queue()
        self.waiting: Dict[str, int] = {}  # session_id → pozisyon
        self.avg_response_time = 20.0      # saniye (zamanla güncellenir)
        self._position_counter = 0

    async def acquire(self, session_id: str):
        """Kuyruğa gir, sıra gelince devam et."""
        self._position_counter += 1
        position = self._position_counter
        self.waiting[session_id] = position
        
        await self.semaphore.acquire()
        del self.waiting[session_id]
        return position

    def release(self, response_time: float = None):
        """İşlem bitti, kilidi bırak."""
        if response_time:
            # Hareketli ortalama
            self.avg_response_time = (
                self.avg_response_time * 0.8 + response_time * 0.2
            )
        self.semaphore.release()

    def get_position(self, session_id: str) -> int:
        return self.waiting.get(session_id, 0)

    def queue_size(self) -> int:
        return len(self.waiting)

    def estimated_wait(self) -> float:
        return self.queue_size() * self.avg_response_time


queue_manager = QueueManager(max_concurrent=1)