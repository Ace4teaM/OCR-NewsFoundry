import asyncio


class MistralRateLimiter:

    def __init__(self, interval: float = 34):
        self.interval = interval
        self.lock = asyncio.Lock()
        self.last_request = 0.0

    async def acquire(self):
        async with self.lock:
            loop = asyncio.get_running_loop()

            now = loop.time()
            delay = self.interval - (now - self.last_request)

            if delay > 0:
                await asyncio.sleep(delay)

            self.last_request = loop.time()


# Une seule instance partagée
mistral_limiter = MistralRateLimiter(interval=2)