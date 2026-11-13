from datetime import date
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, capture_run_messages

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)

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
    search_calls: int = 0
    max_search_calls: int = 3

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

    Utilise les outils à ta disposition pour réaliser tes recherches d'actualités.

    Règles impératives :

    1. Effectue une recherche pertinente pour répondre à la demande.
    2. N'effectue pas plusieurs recherches identiques.
    3. Après réception des résultats, considère la recherche comme terminée.
    4. N'appelle pas de nouveau search_news si une recherche pertinente a déjà été effectuée.
    5. Si aucun article n'est disponible, retourne un résultat vide.
    6. Produis obligatoirement le résultat final après la recherche.


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
    ) -> dict:
    """
    Recherche des actualités sur un sujet donné.

    Args:
        subject: Sujet de recherche obligatoire.
        max_results: Nombre maximum d'articles à récupérer.
    """

    start_date = date.today() - timedelta(days=29) # le plan gratuit ne propose que 30 jours de recherche antérieurs

    # limite le nombre d'appels consecutifs
    if ctx.deps.search_calls >= ctx.deps.max_search_calls:
        print("Nombre maximum de recherches atteint")
        raise ValueError("Nombre maximum de recherches atteint")

    ctx.deps.search_calls += 1

    print("------------------------------------------------------------------")
    print(f"Recherche des actualités pour le sujet : {subject}")
    print(f"Dates utilisées pour la recherche : à partir de {start_date}")
    print("------------------------------------------------------------------")

    news = await wn_receive_news(start_date, None, subject)

    #alimente le contexte avec les articles récupérés
    if news and news.get("available", 0) > 0:
        ctx.deps.add_articles(news)

    return {
        "subject": subject,
        "available": news.get("available", 0),
        "articles_retrieved": len(news.get("news", [])),
        "titles": [
            item.get("title", "")
            for item in news.get("news", [])
            if item.get("title")
        ],
        "message": "Recherche effectuée avec succès."
    }


def build_history(messages: list[dict]):

    history = []

    for item in messages:

        content = item.get("message")

        if not isinstance(content, str) or not content.strip():
            continue

        if item["type"] == "user":
            history.append(
                ModelRequest(
                    parts=[UserPromptPart(content=content)]
                )
            )

        elif item["type"] == "assistant":
            history.append(
                ModelResponse(
                    parts=[TextPart(content=content)]
                )
            )

    return history

async def research(
    message: str,
    messages: list[dict] | None = None,
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
            message_history=build_history(messages or []),
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
