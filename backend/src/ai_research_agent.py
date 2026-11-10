from datetime import date
from pydantic import BaseModel, Field
from pydantic_ai import Agent, capture_run_messages

from ai import model

from worldnews import wn_get_news, wn_receive_news, wn_resume_news
from datetime import date, timedelta

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

class ResearchPlan(BaseModel):
    subject: str = Field(
        description="Sujet principal de la demande.",
        min_length=16
    )

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
    - Si la période est absente ou ambiguë, demande une clarification.
    - N'inventes jamais de dates.

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

research_agent = Agent(
    model,
    instructions="""
    Tu es chargé de rechercher des actualités.

    Tools:
    - Utilise l'outil `search_news` pour récupérer des actualités pertinentes à partir d'un sujet donné.
    - Utilise l'outil `get_news` pour récupérer des articles spécifiques à partir de leurs identifiants.

    Récupére les identifiants des articles à partir de l'historique de conversation.
    Chaque identifiant doit être utilisé avec l'outil `get_news` pour obtenir les détails de l'article.

    La date du jour est fournie dans le prompt.
    """
)


# reraise=True, renvoie l'exception rencontré (sinon RetryError)
@research_agent.tool_plain
@retry(
    stop=stop_after_attempt(2),
    reraise=True,
)
async def search_news(
    subject: str,
    max_results: int = 10
    ) -> str:
    """
    Recherche des actualités sur un sujet donné.

    Args:
        subject: Sujet de recherche obligatoire.
        max_results: Nombre maximum d'articles à récupérer.
    """

    start_date = date.today()
    end_date = date.today() - timedelta(days=29) # le plan gratuit ne propose que 30 jours de recherche antérieurs

    print("------------------------------------------------------------------")
    print(f"Recherche des actualités pour le sujet : {subject}, du {start_date} au {end_date}, max_results = {max_results}")
    print(f"Dates utilisées pour la recherche : du {start_date} au {end_date}")
    print("------------------------------------------------------------------")

    try:
        news = wn_receive_news(start_date, end_date, subject, max=max_results)
        news_summary = wn_resume_news(news)
        return news_summary
    except Exception as e:
        print(str(e))
        return "<Error>impossible d'obtenir les actualités</Error>"


# reraise=True, renvoie l'exception rencontré (sinon RetryError)
@research_agent.tool_plain
@retry(
    stop=stop_after_attempt(2),
    reraise=True, 
)
async def get_news(
    ids: str
    ) -> str:
    """
    Obtient un ou plusieurs articles d'actualités à partir de leurs identifiants.

    Args:
        ids: Identifiants des articles à récupérer, séparés par des virgules.
    """

    print("------------------------------------------------------------------")
    print(f"Recherche de l'article avec l'id : {ids}")
    print("------------------------------------------------------------------")

    try:
        news = wn_get_news(ids)
        news_summary = wn_resume_news(news)
        return news_summary
    except Exception as e:
        print(str(e))
        return f"<Error>impossible d'obtenir les actualités avec les ids {ids}</Error>"


async def research(
    message: str,
) -> str:

    prompt = f"""
    Date du jour : {date.today().isoformat()}

    Répond à la demande suivante :
    {message}
    """

    try:
        with capture_run_messages() as messages:
            result = await research_agent.run(prompt)
            return result.output

    except Exception as e:
        print(f"[AGENT MESSAGES]:")
        for message in messages:
            print(message)

        raise e