
import time
import os
import logging
from contextvars import ContextVar

from httpx import request
import httpx2

from pydantic_ai import Agent
from pydantic_ai.capabilities import Hooks
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from pydantic_ai.retries import (
    AsyncHTTPX2TenacityTransport,
    RetryConfig,
    wait_retry_after,
)
from tenacity import (
    retry_if_exception,
    stop_after_attempt,
    wait_fixed,
)

from rate_limiter import rate_limiter, period

from logger import get_logger

logger = get_logger(__name__)


# ***************************************************************
# Paramètres de configuration

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("La variable GEMINI_API_KEY est manquante")


# ***************************************************************
# Hooks Pydantic AI

hooks = Hooks()


@hooks.on.before_model_request
async def before_model_request(ctx, request_context):

    logger.info(
        "PYDANTIC REQUEST | step=%s | model=%s",
        ctx.run_step,
        request_context.model
    )

    return request_context


@hooks.on.after_model_request
async def after_model_request(ctx, request_context, response):

    logger.info(
        "PYDANTIC RESPONSE | step=%s",
        ctx.run_step
    )

    return response


# ***************************************************************
# Logs

current_agent = ContextVar("current_agent", default="unknown")


def log_retry(retry_state):

    exception = retry_state.outcome.exception()

    logger.warning(
        "RETRY | tentative=%s | prochaine_attente=%s | erreur=%s",
        retry_state.attempt_number,
        retry_state.next_action.sleep,
        exception
    )


async def log_request(request: httpx2.Request):

    logger.info(
        "HTTP REQUEST | agent=%s | %s | %s",
        current_agent.get(),
        request.method,
        request.url
    )


async def log_response(response: httpx2.Response):

    request = response.request

    logger.log(
        logging.ERROR if response.status_code >= 400 else logging.INFO,
        "HTTP RESPONSE | agent=%s | %s | %s | status=%s",
        current_agent.get(),
        request.method,
        request.url,
        response.status_code
    )

    if response.status_code >= 400:

        try:
            await response.aread()
            logger.error("HTTP BODY | %s", response.text)

        except Exception as exc:
            logger.error("HTTP BODY UNAVAILABLE | %s", exc)

    if response.status_code == 429:

        for name, value in response.headers.items():

            if "ratelimit" in name.lower() or name.lower() == "retry-after":
                logger.error("GEMINI LIMIT | %s: %s", name, value)


# ***************************************************************
# Gestion des retries

def should_retry(exception):

    if not isinstance(exception, httpx2.HTTPStatusError):
        return False

    status = exception.response.status_code

    return status == 429 or 500 <= status < 600


def validate_response(response):

    response.raise_for_status()


# ***************************************************************
# Transport avec limitation de débit

class RateLimitedTransport(httpx2.AsyncBaseTransport):

    def __init__(self, limiter, wrapped=None):
        self.limiter = limiter
        self.wrapped = wrapped or httpx2.AsyncHTTPTransport()

    async def handle_async_request(
        self,
        request: httpx2.Request
    ) -> httpx2.Response:
        await self.limiter.acquire()

        start = time.perf_counter()

        print(f"DEBUG | HTTP START | {request.url}")

        response = await self.wrapped.handle_async_request(request)

        print(
            f"DEBUG | HTTP END | "
            f"{response.status_code} | "
            f"{time.perf_counter() - start:.2f}s"
        )

        return response

    async def aclose(self):
        await self.wrapped.aclose()


# ***************************************************************
# Transport Tenacity

transport = AsyncHTTPX2TenacityTransport(
    wrapped=RateLimitedTransport(rate_limiter),
    config=RetryConfig(
        retry=retry_if_exception(should_retry),
        wait=wait_retry_after(
            fallback_strategy=wait_fixed(period / 2),
            max_wait=period,
        ),
        stop=stop_after_attempt(3),
        reraise=True,
        before_sleep=log_retry,
    ),
    validate_response=validate_response
)


# ***************************************************************
# Client HTTP Google


http_client = httpx2.AsyncClient(
    timeout=httpx2.Timeout(1200, connect=5),
    transport=transport,
    event_hooks={
        "request": [log_request],
        "response": [log_response],
    }
)


# ***************************************************************
# Modèle Gemini

model = GoogleModel(
    "gemini-2.5-flash-lite",
    provider=GoogleProvider(
        api_key=api_key,
        http_client=http_client
    )
)


# ***************************************************************
# Agent

agent = Agent(
    model,
    capabilities=[hooks],
    instructions="""
        Tu es un assistant technique.

        Tu réponds en français.
        Tes réponses sont précises et pédagogiques.
    """
)


# ***************************************************************
# Exécution de l'agent

async def prompt_agent(message: str) -> str:

    token = current_agent.set("gemini_agent")

    try:

        result = await agent.run(message)

        return result.output

    finally:
        current_agent.reset(token)
