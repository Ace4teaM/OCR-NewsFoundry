from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

from pydantic_ai.capabilities import Hooks
from pydantic_ai import Agent
from httpx import HTTPStatusError, AsyncClient, AsyncBaseTransport, AsyncHTTPTransport, Request, Response

from contextvars import ContextVar

from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
    wait_exponential
)

from pydantic_ai.retries import (
    AsyncTenacityTransport,
    RetryConfig,
    wait_retry_after
)

import os

from rate_limiter import rate_limiter, max_requests, period


import json
import logging
from logger import get_logger
logger = get_logger(__name__)

# ***************************************************************
# Paramètres de configuration

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise RuntimeError("La variable MISTRAL_API_KEY est manquante")

# ***************************************************************
# Hooks pour les Logs pydantic_ai

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

# information sur les essais dans la console uniquement
def log_retry(retry_state):
    exception = retry_state.outcome.exception()

    print(
        f"RETRY | tentative={retry_state.attempt_number} | prochaine_attente={retry_state.next_action.sleep} s | erreur={exception}"
    )

    if isinstance(exception, HTTPStatusError):
        print(
            f"HTTP ERROR | {exception.request.method} {exception.request.url} | HTTP {exception.response.status_code}"
        )


async def log_request(request: Request):
    logger.info(
        "HTTP REQUEST | agent=%s | %s | %s",
        current_agent.get(),
        request.method,
        request.url
    )


async def log_response(response: Response):
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
                logger.error("MISTRAL LIMIT | %s: %s", name, value)

# ***************************************************************
# Client HTTP personnalisé pour Mistral
# le client permet de géré les appels trops rapprochés à l'API Mistral
# il permet de marquer une pause avant de renouveller l'appel à l'API pour gérer les erreurs 429 (Too Many Requests)
# source: https://pydantic.dev/docs/ai/models/mistral/?utm_source=chatgpt.com
# source: https://pydantic.dev/docs/ai/core-concepts/retries/?utm_source=chatgpt.com

# log les réponses pour DEBUG
def validate_response(response):

    if response.status_code == 429:
        for name, value in response.headers.items():
            if "ratelimit" in name.lower() or name.lower() == "retry-after":
                logger.error("MISTRAL LIMIT | %s: %s", name, value)

    response.raise_for_status()


class RateLimitedTransport(AsyncBaseTransport):

    def __init__(self, limiter, wrapped=None):
        self.limiter = limiter
        self.wrapped = wrapped or AsyncHTTPTransport()

    async def handle_async_request(self, request: Request) -> Response:
        await self.limiter.acquire()

        return await self.wrapped.handle_async_request(request)

    async def aclose(self) -> None:
        await self.wrapped.aclose()

transport = AsyncTenacityTransport(
    wrapped=RateLimitedTransport(rate_limiter),
    config=RetryConfig(
        retry=retry_if_exception_type(HTTPStatusError),
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
# Initialise le modèle Mistral

http_client = AsyncClient(
    timeout=30,
    transport=transport,
    event_hooks={
        "request": [log_request],
        "response": [log_response],
    }
)

model = MistralModel(
    "ministral-3b-latest",
    provider=MistralProvider(
        api_key=api_key,
        http_client=http_client
    )
)

# ***************************************************************
# implémente un agent générique utilisant le modèle Mistral
agent = Agent(
    model,
    capabilities=[hooks],
    instructions="""
        Tu es un assistant technique.

        Tu réponds en français.
        Tes réponses sont précises et pédagogiques.
    """
)

async def prompt_agent(message: str) -> str:
    """
    Analyse une demande utilisateur et retourne son intention structurée.

    Args:
        message: Demande formulée par l'utilisateur.

    Returns:
        Qualification structurée de la demande.
    """

    token = current_agent.set(__name__)

    try:
        result = await agent.run(message)

        return result.output
    
    finally:
        current_agent.reset(token)
