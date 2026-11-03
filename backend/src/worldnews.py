import os
from urllib import response
import requests
from datetime import datetime, timedelta

WORLDNEWS_API_KEY = os.getenv("WORLDNEWS_API_KEY")

if not WORLDNEWS_API_KEY:
    raise RuntimeError("La variable WORLDNEWS_API_KEY est manquante")


def wn_receive_news(start: datetime, end: datetime, subject:str = None, category:str = None, max: int = 10, timeout: int = 30) -> dict:
    """
    Récupère les articles de presse sur une période donnée.

    Args:
        start: Date de début.
        end: Date de fin.
        subject: Sujet principal des articles.
        category: Catégorie des articles.
        max: Nombre maximum d'articles.
        timeout: Délai d'attente pour la requête en secondes.

    Returns:
        Réponse JSON de World News API.

    Raises:
        RuntimeError: Si la récupération des articles échoue.
    """
    formatted_start = start.strftime("%Y-%m-%d %H:%M:%S")
    formatted_end = end.strftime("%Y-%m-%d %H:%M:%S")

    params = {
        "api-key": WORLDNEWS_API_KEY,
        "language": "fr",
        "earliest-publish-date": formatted_start,
        "latest-publish-date": formatted_end,
        "number": max # limite le nombre d'articles recus
    }

    if subject:
        params["text"] = subject
        
    #if category:
    #    params["categories"] = category

    response = requests.get(
        "https://api.worldnewsapi.com/search-news",
        params=params,
        timeout=timeout,
    )

    response.raise_for_status() 
    return response.json()


def wn_resume_news(news: dict) -> str:
    """
    Formate les articles récupérés pour leur transmission à un agent IA.

    Args:
        news: Réponse JSON de World News API.

    Returns:
        Texte contenant les titres, résumés et dates des articles.
    """
    articles = news.get("news", [])
    content = ""
    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")
        publish_date = article.get("publish_date", "")
        content += f"Titre: {title}\nRésumé: {summary}\nDate de publication: {publish_date}\n\n"
    return content
