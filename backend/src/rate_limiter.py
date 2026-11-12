import asyncio
from collections import deque
import os


# ***************************************************************
# Paramètres de configuration

max_requests = int(os.getenv("QUOTA_REQUESTS", 1))
period = float(os.getenv("QUOTA_PERIOD", 34))


# ***************************************************************
# Limiteur

class RateLimiter:

    def __init__(self, max_requests: int = 2, period: float = 60):
        if max_requests < 1:
            raise ValueError("max_requests doit être supérieur ou égal à 1")

        if period <= 0:
            raise ValueError("period doit être supérieur à 0")

        self.max_requests = max_requests
        self.period = period
        self.lock = asyncio.Lock()
        self.requests = deque()

    async def acquire(self) -> None:
        """
        Attend qu'une place soit disponible dans la fenêtre glissante.
        """

        async with self.lock:
            loop = asyncio.get_running_loop()

            while True:
                now = loop.time()

                # Supprime les requêtes sorties de la fenêtre glissante
                while (
                    self.requests
                    and now - self.requests[0] >= self.period
                ):
                    self.requests.popleft()

                if len(self.requests) < self.max_requests:
                    self.requests.append(now)

                    print(
                        f"DEBUG | RATE LIMIT | "
                        f"Requête autorisée "
                        f"({len(self.requests)}/{self.max_requests})"
                    )

                    return

                delay = self.period - (now - self.requests[0])

                print(
                    f"DEBUG | RATE LIMIT | "
                    f"Quota atteint | "
                    f"Attente : {delay:.2f}s"
                )

                await asyncio.sleep(max(delay, 0.01))


# Une seule instance partagée
rate_limiter = RateLimiter(
    max_requests=max_requests,
    period=period
)