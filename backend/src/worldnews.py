import os
import json
from tracemalloc import start
from urllib import response
from datetime import datetime, timedelta
from fastapi import params
import httpx
from pydantic import BaseModel, Field
from pprint import pprint
import logging
import time
from pathlib import Path



from logger import get_logger

logger = get_logger(__name__)

WORLDNEWS_API_KEY = os.getenv("WORLDNEWS_API_KEY")

if not WORLDNEWS_API_KEY:
    raise RuntimeError("La variable WORLDNEWS_API_KEY est manquante")

WORLDNEWS_SIMULATE = os.getenv("WORLDNEWS_SIMULATE", "false").lower() == "true"
WORLDNEWS_FIXTURE = Path("worldnews.sample.json")

# données retourné par world news API
class Article(BaseModel):
    id: int | str
    title: str
    text: str | None = None
    summary: str | None = None
    url: str | None = None
    publish_date: datetime | None = None
    authors: list[str] = Field(default_factory=list)
    image: str | None = None


async def request_worldnews(
    endpoint: str,
    params: dict,
    timeout: int = 30
) -> dict:
    """Exécute une requête HTTP vers World News API et journalise son résultat."""

    url = f"https://api.worldnewsapi.com/{endpoint}"
    start = time.perf_counter()

    # Simulation
    if WORLDNEWS_SIMULATE:
        logger.info("WORLDNEWS SIMULATION | %s", endpoint)

        with WORLDNEWS_FIXTURE.open("r", encoding="utf-8") as file:
            return json.load(file)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:

            response = await client.get(url, params=params)

            duration = (time.perf_counter() - start) * 1000

            params = dict(response.request.url.params)
            params["api-key"] = "***"

            logger.log(
                logging.ERROR if response.status_code >= 400 else logging.INFO,
                "GET %s | HTTP %s | %.2f ms",
                params,
                response.status_code,
                duration
            )

            if not response.is_success:
                logger.error(
                    "WORLDNEWS ERROR | %s",
                    response.text
                )

                response.raise_for_status()

            return response.json()

    except httpx.HTTPStatusError:
        raise

    except httpx.RequestError:
        logger.exception(
            "WORLDNEWS REQUEST ERROR | GET %s",
            url
        )
        raise

async def wn_receive_news(start: datetime, end: datetime = None, subject:str = None, timeout: int = 30) -> dict:
    """
    Récupère les articles de presse sur une période donnée.

    Args:
        start: Date de début.
        end: Date de fin.
        subject: Sujet principal des articles.
        category: Catégorie des articles.
        timeout: Délai d'attente pour la requête en secondes.

    Returns:
        Réponse JSON de World News API.

    Raises:
        RuntimeError: Si la récupération des articles échoue.
    """
    formatted_start = start.strftime("%Y-%m-%d %H:%M:%S")

    params = {
        "api-key": WORLDNEWS_API_KEY,
        "language": "fr",
        "earliest-publish-date": formatted_start,
    }

    if end:
        formatted_end = end.strftime("%Y-%m-%d %H:%M:%S")
        params["latest-publish-date"] = formatted_end
        
    if subject:
        params["text"] = subject
        
    print("************************************************")
    print("World News API")
    pprint(params, indent=2)
    print("************************************************")

    return await request_worldnews(
        "search-news",
        params,
        timeout
    )


async def wn_get_news(ids: str, timeout: int = 30) -> dict:
    """
    Récupère un article de presse par son identifiant.

    Args:
        ids: Identifiants des articles à récupérer, séparés par des virgules.
        timeout: Délai d'attente pour la requête en secondes.

    Returns:
        Réponse JSON de World News API.

    Raises:
        RuntimeError: Si la récupération des articles échoue.
    """

    params = {
        "api-key": WORLDNEWS_API_KEY,
        "language": "fr",
        "ids": ids
    }

    print("************************************************")
    print("World News API")
    pprint(params, indent=2)
    print("************************************************")

    return await request_worldnews(
        "retrieve-news",
        params,
        timeout
    )



def wn_resume_news(news: dict | list[Article]) -> str:
    """
    Formate les articles récupérés pour leur transmission à un agent IA.

    Args:
        news: Réponse JSON de World News API.

    Returns:
        Texte contenant les titres, résumés et dates des articles.
    """
    if isinstance(news, dict):
        articles = news.get("news", [])
    else:
        articles = news

    content = ""
    for article in articles:
        # convertie Article en dictionnaire si nécessaire
        if isinstance(article, Article):
            article = article.model_dump()

        id = article.get("id", "")
        category = article.get("category", "")
        title = article.get("title", "")
        summary = article.get("summary", "")
        publish_date = article.get("publish_date", "")
        content += f"# {title}\n\n* Identifiant: {id}\n* Catégorie: {category}\n* Date de publication: {publish_date}\n\nRésumé:\n{summary}\n\n\n"
    return content
