import os
from dataclasses import dataclass
import json
from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from database import init_db, engine

from fastapi import FastAPI, HTTPException, status, Response, Cookie, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlmodel import Session, insert, select
import bcrypt
import uvicorn
from models import Chat, User, Revue
import bcrypt
import jwt
from ai import prompt_agent
from ai_synthesis_agent import synthesize_news
from ai_classify_agent import Action, classify_user_request, period_to_dates
from ai_research_agent import research
from ai_revues_agent import synthesize_revues
from worldnews import Article, wn_receive_news, wn_resume_news
from errors import AppError, handle_api_error
import sys
from result import Result
import time

import logging
from logger import get_logger
logger = get_logger("http")

import traceback

app = FastAPI()


@app.middleware("http")
async def log_requests(request: Request, call_next):

    start = time.perf_counter()

    try:
        response = await call_next(request)

        duration = (time.perf_counter() - start) * 1000

        logger.log(
            logging.ERROR if response.status_code >= 400 else logging.INFO,
            "%s %s | %s | %.2f ms",
            request.method,
            request.url.path,
            response.status_code,
            duration
        )

        return response

    except Exception:
        duration = (time.perf_counter() - start) * 1000

        logger.exception(
            "%s %s | EXCEPTION | %.2f ms",
            request.method,
            request.url.path,
            duration
        )

        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ["ALLOW_ORIGINS"].split("|"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
COOKIE_SAMESITE = "none" if COOKIE_SECURE else "lax"
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
CAN_USE_PARTITIONED_COOKIES = sys.version_info >= (3, 14)

bearer_scheme = HTTPBearer()


class LoginRequest(BaseModel):
    """Données nécessaires à l'authentification d'un utilisateur."""
    email: str
    password: str

class CreateMessage(BaseModel):
    """Données nécessaires à la création d'un message."""
    message: str

class CreateChat(BaseModel):
    """Données nécessaires à la création d'un chat."""
    title: str
    message: str | None = None

class CreateRevue(BaseModel):
    """Données nécessaires à la création d'une revue de presse."""
    theme: str

@dataclass
class ResponseApi():
    """Données d'une réponse structurée de l'API"""
    success: bool
    message: str
    data: dict | None = None


def create_access_token(user_id: int) -> str:
    """
    Génère un JWT signé pour un utilisateur authentifié.

    Le jeton contient l'identifiant de l'utilisateur, sa date de création
    et sa date d'expiration.

    Args:
        user_id: Identifiant de l'utilisateur en base de données.

    Returns:
        Le JWT signé sous forme de chaîne de caractères.
    """
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )



def get_current_user(
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """
    Authentifie l'utilisateur à partir du JWT contenu dans le cookie.

    Vérifie la signature et l'expiration du jeton, puis recherche
    l'utilisateur correspondant dans la base de données.

    Args:
        access_token: JWT transmis automatiquement par le navigateur
            dans le cookie HTTP-only.

    Returns:
        L'objet User correspondant au jeton valide.

    Raises:
        HTTPException: Si le cookie est absent, le jeton est invalide
            ou expiré, ou si l'utilisateur n'existe plus.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
        )

    try:
        payload = jwt.decode(
            access_token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        subject = payload.get("sub")
        if not subject:
            raise jwt.InvalidTokenError("Missing subject")

        user_id = int(subject)
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton invalide ou expiré",
        )

    with Session(engine) as session:
        user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
        )

    return user


async def prompt(prompt: str, chat: Chat | None, session: Session | None, current_user: User):
    """
    Nouvelle demande de l'utilisateur.

    Analyse la demande de l'utilisateur et tente de déterminer le contexte et l'intention.

    Args:
        prompt: Message envoyé par l'utilisateur.
        chat: Objet Chat contenant l'historique des messages précédents. Peut être None si aucun historique n'est disponible.
        session: Session SQLAlchemy pour les opérations sur la base de données.
        current_user: Utilisateur actuellement authentifié.

    Returns:
        Résultat de la demande, peut être retourné avec ResponseApi().

    Raises:
        HTTPException: Si l'utilisateur n'est pas authentifié.
    """

    prompt = prompt.strip() if prompt else None
    if not prompt:
        yield Result(
            success=False,
            message="Le message ne peut pas être vide.",
            data=None
        )
        return

    print("************************************************")
    print("Demande initiale:", prompt)
    print("************************************************")

    # objet créé
    message = None
    response = None
    revue = None

    # historique des messages précédents
    messages = json.loads(chat.messages) if chat else []

    # archive le prompt
    messages.append({
        "date": datetime.now(timezone.utc).isoformat(),
        "type": "user",
        "message": prompt
    })

    # agent de qualification
    # appel LLM pour obtenir une demande structurée
    try:
        yield Result(
            success=True,
            message="Détermine le contexte de la demande...",
            data=None
        )

        context = await classify_user_request(prompt, messages)
        print("************************************************")
        print("Contexte obtenu:", context.model_dump_json(indent=2))
        print("************************************************")
    except Exception as e:
        yield Result(
            success=False,
            message="Impossible de déterminer le contexte de la demande",
            data={
                "prompt": prompt,
                "erreur": str(e)
            }
        )
        return

    try:
        match context.action:
            # La réponse est connue
            case Action.RESPOND:
                if context.response:
                    response=context.response

            # demande une recherche d'actualités
            case Action.NEWS_SEARCH | Action.NEWS_QUESTION:
                yield Result(
                    success=True,
                    message="Recherche d'actualités...",
                    data=None
                )

                # ajoute du contexte à la discution
                # récupère les actualités du jour depuis l'API World News
                start, end = period_to_dates(
                    context.period,
                    context.period_start,
                    context.period_end,
                )

                # si les dates ne sont pas spécifiées, on réalise une recherche via les outils de recherche d'actualités
                if start is None or end is None:
                    # recherche des résultats
                    results = await research(context.subject, messages)

                    if len(results.articles) == 0:
                        raise AppError("Aucun résultat trouvé pour la recherche d'actualités.")

                    news_summary = wn_resume_news(results.articles)

                    messages.append({
                        "date": datetime.now(timezone.utc).isoformat(),
                        "message": news_summary,
                        "type": "system"
                    })
                # si les dates sont connues, on récupére les articles aupres de WorldNews directement
                else:
                    day_news = await wn_receive_news(start, end, context.subject)

                    if "available" not in day_news or day_news.get("available", 0) == 0:
                        raise AppError("Aucun résultat trouvé pour la recherche d'actualités.")

                    news_summary = wn_resume_news(day_news)

                    messages.append({
                        "date": datetime.now(timezone.utc).isoformat(),
                        "message": news_summary,
                        "type": "system"
                    })

                yield Result(
                    success=True,
                    message="Synthétise les résultats...",
                    data=None
                )

                # synthetise uniquement le contexte en cours
                response = await synthesize_news(messages[-1:], message)

            case Action.RESYNTHESIZE:
                yield Result(
                    success=True,
                    message="Synthétise la conversation...",
                    data=None
                )

                # interoge le LLM avec le message de l'utilisateur
                if messages:
                    response = await synthesize_news(messages, message)
                else:
                    raise AppError("Aucun chat existant pour synthétiser les actualités.")

            # La réponse est connue
            case Action.CLARIFY:
                if context.question:
                    response=context.question

            case Action.GENERAL_QUESTION:
                yield Result(
                    success=True,
                    message="Réflexion en cours...",
                    data=None
                )

                # interoge le LLM avec le message de l'utilisateur
                response = await prompt_agent(message)

            case Action.OUT_OF_SCOPE:
                response = "Je ne suis pas sûr de pouvoir répondre à cette question. Veuillez poser une question sur l'actualité."

            case Action.END:
                response = "Très bien, terminons la conversation."

            case Action.MAKE_REVIEW:
                # chat existant ?
                if chat:
                    yield Result(
                        success=True,
                        message="Synthétise la conversation...",
                        data=None
                    )

                    synthese = await synthesize_revues(
                        theme=context.subject,
                        messages=messages
                    )

                    if not synthese.sufficient:
                        raise AppError(f"Les articles sur le thème {context.subject} sont insuffisants pour générer une revue de presse")
                    else:
                        revue = Revue(
                            user_id=current_user.id,
                            theme=context.subject,
                            content=synthese.content
                        )
                        message = "Revue de presse générée avec succès."
                # si pas de chat, on recherche des actualités
                else:
                    yield Result(
                        success=True,
                        message="Recherche des actualités...",
                        data=None
                    )

                    # recherche des résultats
                    results = await research(context.subject)

                    news_summary = wn_resume_news(results.articles)

                    messages.append({
                        "date": datetime.now(timezone.utc).isoformat(),
                        "message": news_summary,
                        "type": "system"
                    })
                    
                    yield Result(
                        success=True,
                        message="Synthétise les actualités...",
                        data=None
                    )

                    resume = await synthesize_news(messages, message)
                    
                    revue = Revue(
                        user_id=current_user.id,
                        theme=context.subject,
                        content=resume
                    )
                    message = "Revue de presse générée avec succès."

            case _:
                raise AppError("Je ne parviens pas à déterminer le sens de votre question. Pouvez vous reformuler votre question ?")

    except Exception as e:
        traceback.print_exc()
        
        app_error = handle_api_error(e)
        app_error.print_debug()
        
        logger.error(
            "%s | %s | %s",
            str(e),
            app_error.message,
            app_error.details
        )

        yield Result(
            success=False,
            message=app_error.message,
            data={
                "prompt": prompt,
                "erreur": str(app_error)
            }
        )
        return


    if response:

        messages.append({
            "date": datetime.now(timezone.utc).isoformat(),
            "type": "assistant",
            "message": response
        })

        # Si le chat existe, la conversation continue
        if chat:
            chat.messages=json.dumps(messages)
        # sinon le chat est créé
        else:
            chat = Chat(
                user_id=current_user.id,
                title="Nouvelle discussion",
                messages=json.dumps(messages)
            )

        session.add(chat)
        session.commit()
        session.refresh(chat)


        yield Result(
            success=True,
            message="Conversation générée avec succès.",
            data={
                "response": response,
                "chat": chat
            }
        )
        return

    if revue:
        session.add(revue)
        session.commit()
        session.refresh(revue)

        yield Result(
            success=True,
            message="Revue de presse générée avec succès.",
            data={
                "revue": revue
            }
        )
        return

    yield Result(
        success=False,
        message="Impossible de répondre à la demande.",
        data={}
    )
    return


@app.get("/")
async def hello():
    return ResponseApi(success = True, message = "👋")



@app.post("/login")
async def login(credentials: LoginRequest, response: Response):
    """
    Authentifie un utilisateur et crée son cookie de session JWT.

    Recherche l'utilisateur par son adresse e-mail et vérifie son
    mot de passe à l'aide de bcrypt. Si les identifiants sont valides,
    génère un JWT et le place dans un cookie HTTP-only.

    Args:
        credentials: Adresse e-mail et mot de passe fournis par le client.
        response: Réponse HTTP utilisée pour définir le cookie.

    Returns:
        Un message confirmant la connexion.

    Raises:
        HTTPException: Si l'adresse e-mail ou le mot de passe est incorrect.
    """
    with Session(engine) as session:
        statement = select(User).where(
            User.email == credentials.email
        )
        user = session.exec(statement).first()

        if user is None or not bcrypt.checkpw(
            credentials.password.encode("utf-8"),
            user.hashed_password.encode("utf-8"),
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect",
            )

        access_token = create_access_token(user.id)

        print("Python version:", sys.version)
        print("COOKIE_SECURE:", COOKIE_SECURE)
        print("COOKIE_SAMESITE:", COOKIE_SAMESITE)
        print("PARTITIONED:", CAN_USE_PARTITIONED_COOKIES)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE, # none, permet en production d'envoyer le cookie cross-site
            partitioned=CAN_USE_PARTITIONED_COOKIES, # permet de conserver des cookies tiers, mais en les isolant par site 
            max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

        return ResponseApi(success=True, message="Connexion réussie", data={
            "id": user.id,
            "email": user.email,
        })

@app.post("/logout")
async def logout(response: Response):
    """
    Déconnecte l'utilisateur en supprimant son cookie JWT.

    Args:
        response: Réponse HTTP utilisée pour supprimer le cookie.

    Returns:
        Un message confirmant la déconnexion.
    """
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE, # none, permet en production d'envoyer le cookie cross-site
    )

    return ResponseApi(success=True, message="Déconnexion réussie")

@app.get("/me")
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Retourne les informations du compte actuellement authentifié.

    L'utilisateur est identifié et validé par la dépendance
    get_current_user avant l'exécution de cette fonction.

    Args:
        current_user: Utilisateur authentifié récupéré depuis la BDD.

    Returns:
        L'identifiant et l'adresse e-mail de l'utilisateur.
    """
    
    return ResponseApi(success=True, message="Utilisateur authentifié", data={
        "id": current_user.id,
        "email": current_user.email,
    })


@app.post("/chats")
async def chats(data: CreateChat, current_user: Annotated[User, Depends(get_current_user)]):
    """
    Crée un nouveau chat pour l'utilisateur authentifié.

    Args:
        current_user: Utilisateur actuellement authentifié.

    Returns:
        Un message confirmant la création du chat.
        Le dictionnaire de données contient l'identifiant du chat créé.

    Raises:
        HTTPException: Si l'utilisateur n'est pas authentifié.
    """

    # crée un nouveau chat si nécessaire

    messages = []

    response = "Comment puis je vous aider ? Posez moi une question sur l'actualité."
    
    messages.append({
        "date": datetime.now(timezone.utc).isoformat(),
        "message": response,
        "type": "assistant"
    })

    with Session(engine) as session:
        chat = Chat(
            user_id=current_user.id,
            title=data.title,
            messages=json.dumps(messages)
        )

        session.add(chat)
        session.commit()
        session.refresh(chat)

        return ResponseApi(
            success=True,
            message="Chat créé avec succès",
            data=chat
        )


@app.get("/chats")
async def get_chats(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    retourne les chats d'un utilisateur authentifié.

    L'utilisateur est identifié et validé par la dépendance
    get_current_user avant l'exécution de cette fonction.

    Args:
        current_user: Utilisateur authentifié récupéré depuis la BDD.

    Returns:
        L'historique des chats.
    """
    with Session(engine) as session:
        statement = select(Chat.id, Chat.title, Chat.created_at).where(
            Chat.user_id == current_user.id
        )
        chats = session.exec(statement).all()
        
        return ResponseApi(success=True, message="Chats trouvés", data=[
            {
                "id": chat.id,
                "title": chat.title,
                "created_at": chat.created_at,
            }
            for chat in chats
        ])
    

@app.get("/chats/{chat_id}")
async def get_chat(
    chat_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    retourne l'historique de la discussion pour l'afficher à l'utilisateur

    L'utilisateur est identifié et validé par la dépendance
    get_current_user avant l'exécution de cette fonction.

    Args:
        chat_id: Identifiant du chat dont on souhaite récupérer l'historique.
        current_user: Utilisateur authentifié récupéré depuis la BDD.

    Returns:
        L'historique des messages du chat spécifié.
    """
    with Session(engine) as session:
        chat = session.get(Chat, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat introuvable")
        if chat.user_id != current_user.id:
            raise HTTPException(status_code=401, detail="Non autorisé")
        return ResponseApi(success=True, message="Chat trouvé", data={
            "id": chat.id,
            "title": chat.title,
            "created_at": chat.created_at,
            "messages": chat.messages,
        })


@app.post("/prompt")
async def user_prompt(
    data: CreateMessage,
    current_user: Annotated[User, Depends(get_current_user)]
):

    with Session(engine) as session:
        result = None

        async for item in prompt(
            data.message,
            None,
            session,
            current_user
        ):
            result = item

        return ResponseApi(result.success, result.message, result.data)


@app.post("/prompt_stream")
async def user_prompt_stream(
    data: CreateMessage,
    current_user: Annotated[User, Depends(get_current_user)]
):

    async def generate():

        with Session(engine) as session:

            async for result in prompt(
                data.message,
                None,
                session,
                current_user
            ):
                response = ResponseApi(
                    result.success,
                    result.message,
                    result.data
                )

                yield json.dumps(jsonable_encoder(response)) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson" # Newline Delimited JSON
    )

@app.post("/chats/{chat_id}/messages")
async def create_message(
    chat_id: int,
    data: CreateMessage,
    current_user: Annotated[User, Depends(get_current_user)]
):
    with Session(engine) as session:
        chat = session.get(Chat, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat introuvable")
        if chat.user_id != current_user.id:
            raise HTTPException(status_code=401, detail="Non autorisé")

        result = None

        async for item in prompt(
            data.message,
            chat,
            session,
            current_user
        ):
            result = item

        return ResponseApi(result.success, result.message, result.data)


@app.post("/chats/{chat_id}/messages_stream")
async def create_message_stream(
    chat_id: int,
    data: CreateMessage,
    current_user: Annotated[User, Depends(get_current_user)]
):

    with Session(engine) as session:
        chat = session.get(Chat, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat introuvable")
        if chat.user_id != current_user.id:
            raise HTTPException(status_code=401, detail="Non autorisé")

        async def generate():

            async for result in prompt(
                data.message,
                chat,
                session,
                current_user
            ):
                response = ResponseApi(
                    result.success,
                    result.message,
                    result.data
                )

                encoded = json.dumps(jsonable_encoder(response))

                yield encoded + "\n"

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson" # Newline Delimited JSON
        )

@app.post("/chats/{chat_id}/revues")
async def create_revue(
    chat_id: int,
    revue_data: CreateRevue,
    current_user: Annotated[User, Depends(get_current_user)]
):
    with Session(engine) as session:

        # Vérifie que le chat appartient à l'utilisateur
        chat = session.exec(
            select(Chat).where(
                Chat.id == chat_id,
                Chat.user_id == current_user.id
            )
        ).first()

        if not chat:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Action non autorisée",
            )

        revue = await synthesize_revues(
            theme=revue_data.theme,
            messages=json.loads(chat.messages) if chat.messages else []
        )

        if not revue.sufficient:
            return ResponseApi(success=False, message=f"Les articles sur le thème {revue_data.theme} sont insuffisants pour générer une revue de presse", data={
                "response": revue.response
            })

        revue = Revue(
            user_id=current_user.id,
            theme=revue_data.theme,
            content=revue.content
        )

        session.add(revue)
        session.commit()
        session.refresh(revue)

        return ResponseApi(success=True, message="Revue de presse générée avec succès", data=revue)


@app.get("/revues")
def get_revues(
    current_user: Annotated[User, Depends(get_current_user)]
):
    with Session(engine) as session:

        revues = session.exec(
            select(Revue)
            .where(Revue.user_id == current_user.id)
            .order_by(Revue.created_at.desc())
        ).all()

        return ResponseApi(success=True, message="Revues trouvées", data=revues)

if __name__ == "__main__":
    init_db()

    uvicorn.run(app, host="0.0.0.0", port=8000)
