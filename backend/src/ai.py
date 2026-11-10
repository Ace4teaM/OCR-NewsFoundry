from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider
from httpx import HTTPStatusError, AsyncClient

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

# ***************************************************************
# Paramètres de configuration

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise RuntimeError("La variable MISTRAL_API_KEY est manquante")

# ***************************************************************
# Client HTTP personnalisé pour Mistral
# le client permet de géré les appels trops rapprochés à l'API Mistral
# il permet de marquer une pause avant de renouveller l'appel à l'API pour gérer les erreurs 429 (Too Many Requests)
# source: https://pydantic.dev/docs/ai/models/mistral/?utm_source=chatgpt.com
# source: https://pydantic.dev/docs/ai/core-concepts/retries/?utm_source=chatgpt.com

def log_retry(retry_state):
    exception = retry_state.outcome.exception()

    print(
        f"[LLM RETRY] Erreur : {exception} | "
        f"Tentative : {retry_state.attempt_number} | "
        f"Nouvel essai dans : {retry_state.next_action.sleep}s | "
    )

def validate_response(response):
    if response.status_code == 429:
        print("[HTTP ERROR] Status: 429 - Too Many Requests")
        response.raise_for_status()

transport = AsyncTenacityTransport(
    config=RetryConfig(
        retry=retry_if_exception_type(HTTPStatusError),
        wait=wait_retry_after(
            fallback_strategy=wait_exponential(
                multiplier=5,
                max=60,
            ),
            max_wait=120,
        ),
        stop=stop_after_attempt(4),
        reraise=True,
        before_sleep=log_retry,
    ),
    validate_response=validate_response
)

# ***************************************************************
# Initialise le modèle Mistral

http_client = AsyncClient(timeout=30, transport=transport)

model = MistralModel(
    "ministral-3b-latest",
    provider=MistralProvider(
        api_key=os.environ["MISTRAL_API_KEY"],
        http_client=http_client
    ),
)

# ***************************************************************
# implémente un agent générique utilisant le modèle Mistral
agent = Agent(
    model,
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

    result = await agent.run(message)

    return result.output
