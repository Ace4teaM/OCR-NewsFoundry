from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

import os

api_key = os.getenv("MISTRAL_API_KEY")

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