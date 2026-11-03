from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

import os

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise RuntimeError("La variable MISTRAL_API_KEY est manquante")

model = MistralModel(
    "ministral-3b-latest",
    provider=MistralProvider(
        api_key=os.environ["MISTRAL_API_KEY"]
    ),
)


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
