from datetime import date
from pydantic import BaseModel
from pydantic_ai import Agent

from ai import model

class ResearchPlan(BaseModel):
    subject: str
    start_date: date | None = None
    end_date: date | None = None
    category: str | None = None
    requires_clarification: bool = False
    clarification_question: str | None = None


research_planner_agent = Agent(
    model,
    output_type=ResearchPlan,
    instructions="""
    Tu es chargé de préparer les paramètres d'une recherche d'actualités.

    À partir du contexte de conversation :
    - Identifie le sujet de la recherche.
    - Identifie la date de début et la date de fin.
    - Identifie éventuellement une catégorie.
    - Si la période est absente, utilise les 7 derniers jours.
    - Si la période est ambiguë, demande une clarification.
    - N'invente jamais de dates.

    La date du jour est fournie dans le prompt.
    """
)


async def prepare_research(
    conversation_context: str,
) -> ResearchPlan:

    prompt = f"""
    Date du jour : {date.today().isoformat()}

    Contexte de conversation :
    {conversation_context}

    Prépare les paramètres de recherche.
    """

    result = await research_planner_agent.run(prompt)

    return result.output