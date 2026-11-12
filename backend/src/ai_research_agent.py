from datetime import date, datetime
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, capture_run_messages
from dataclasses import dataclass, field

from ai import model, current_agent, hooks

from worldnews import Article, wn_get_news, wn_receive_news, wn_resume_news
from datetime import date, timedelta

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class ResearchResult(BaseModel):
    subject: str
    articles: list[Article]

@dataclass
class ResearchDeps:
    subject: str
    articles: dict[str, Article] = field(default_factory=dict)

    def add_articles(self, news: dict) -> None:
        """Ajoute les articles retournés par World News API."""
        for item in news.get("news", []):
            article = Article.model_validate(item)
            self.articles[str(article.id)] = article


research_agent = Agent(
    model,
    capabilities=[hooks],
    deps_type=ResearchDeps,
    output_type=ResearchResult,
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
@research_agent.tool
@retry(
    stop=stop_after_attempt(2),
    reraise=True,
)
async def search_news(
    ctx: RunContext[ResearchDeps],
    subject: str,
    max_results: int = 10,
    ) -> dict:
    """
    Recherche des actualités sur un sujet donné.

    Args:
        subject: Sujet de recherche obligatoire.
        max_results: Nombre maximum d'articles à récupérer.
    """

    start_date = date.today() - timedelta(days=29) # le plan gratuit ne propose que 30 jours de recherche antérieurs

    print("------------------------------------------------------------------")
    print(f"Recherche des actualités pour le sujet : {subject}, max_results = {max_results}")
    print(f"Dates utilisées pour la recherche : à partir de {start_date}")
    print("------------------------------------------------------------------")

    news = await wn_receive_news(start_date, None, subject, max=max_results)

    #alimente le contexte avec les articles récupérés
    if news and news.get("available", 0) > 0:
        ctx.deps.add_articles(news)

    return news


# reraise=True, renvoie l'exception rencontré (sinon RetryError)
@research_agent.tool
@retry(
    stop=stop_after_attempt(2),
    reraise=True, 
)
async def get_news(
    ctx: RunContext[ResearchDeps],
    ids: str
    ) -> dict:
    """
    Obtient un ou plusieurs articles d'actualités à partir de leurs identifiants.

    Args:
        ids: Identifiants des articles à récupérer, séparés par des virgules.
    """

    print("------------------------------------------------------------------")
    print(f"Recherche de l'article avec l'id : {ids}")
    print("------------------------------------------------------------------")

    news =  await wn_get_news(ids)

    #alimente le contexte avec les articles récupérés
    if news and news.get("available", 0) > 0:
        ctx.deps.add_articles(news)

    return news

async def research(
    message: str,
) -> ResearchResult:

    deps = ResearchDeps(subject=message)

    prompt = f"""
    Date du jour : {date.today().isoformat()}

    Répond à la demande suivante :
    {message}
    """

    token = current_agent.set(__name__)

    try:
        result = await research_agent.run(
            prompt,
            deps=deps
        )

        print("************************************************")
        print("Articles toruvés:", len(deps.articles))
        print("************************************************")

        return ResearchResult(
            subject=deps.subject,
            articles=list(deps.articles.values())
        )
        
    finally:
        current_agent.reset(token)
