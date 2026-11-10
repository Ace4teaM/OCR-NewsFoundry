import os
from tracemalloc import start
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

    print(params)

    response = requests.get(
        "https://api.worldnewsapi.com/search-news",
        params=params,
        timeout=timeout,
    )

    if not response.ok:
        print("Code HTTP :", response.status_code)
        print("Réponse API :", response.text)

        response.raise_for_status()

    return response.json()


def wn_get_news(ids: str, timeout: int = 30) -> dict:
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

    print(params)

    response = requests.get(
        "https://api.worldnewsapi.com/retrieve-news",
        params=params,
        timeout=timeout,
    )

    if not response.ok:
        print("Code HTTP :", response.status_code)
        print("Réponse API :", response.text)

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
        id = article.get("id", "")
        category = article.get("category", "")
        title = article.get("title", "")
        summary = article.get("summary", "")
        publish_date = article.get("publish_date", "")
        content += f"Titre: {title}\nIdentifiant: {id}\nCatégorie: {category}\nDate de publication: {publish_date}\nRésumé: {summary}\n\n"
    return content
