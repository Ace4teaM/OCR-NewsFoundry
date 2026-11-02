import os
import requests
from datetime import datetime, timedelta

WORLDNEWS_API_KEY = os.getenv("WORLDNEWS_API_KEY")

if not WORLDNEWS_API_KEY:
    raise RuntimeError("La variable WORLDNEWS_API_KEY est manquante")


def wn_receive_day_news() -> dict:
    date = datetime.now() - timedelta(days=1)
    formatted_date = date.strftime("%Y-%m-%d %H:%M:%S")

    response = requests.get(
        "https://api.worldnewsapi.com/search-news",
        params={
            "api-key": WORLDNEWS_API_KEY,
            "language": "fr",
            "earliest-publish-date": formatted_date,
            "number": 10 # limite le nombre d'articles recus
        })

    return response.json()

def wn_resume_day_news(news: dict) -> str:
    articles = news.get("news", [])
    content = ""
    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")
        publish_date = article.get("publish_date", "")
        content += f"Titre: {title}\nRésumé: {summary}\nDate de publication: {publish_date}\n\n"
    return content
