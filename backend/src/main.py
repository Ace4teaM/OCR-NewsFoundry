from email import message
from textwrap import dedent
from requests.exceptions import HTTPError
import os
from dataclasses import dataclass
import json
from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from database import init_db, engine
from fastapi import FastAPI, HTTPException, status, Response, Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, insert, select
import bcrypt
import uvicorn
from models import Chat, User, Revue
import bcrypt
import jwt
from ai import prompt_agent
from ai_synthesis_agent import synthesize_news
from ai_classify_agent import Intent, classify_user_request, period_to_dates
from ai_conversation_agent import manage_conversation, ConversationAction
from ai_research_agent import prepare_research, ResearchPlan, research
from ai_revues_agent import synthesize_revues
from worldnews import wn_receive_news, wn_resume_news
from pydantic_ai.exceptions import ModelHTTPError, ModelAPIError
from errors import AppError, handle_api_error

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ["ALLOW_ORIGINS"].split("|"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

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

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=os.getenv("COOKIE_SECURE", "true").lower() == "true",
            samesite="none", # none, permet en production d'envoyer le cookie cross-site
            partitioned=True, # permet de conserver des cookies tiers, mais en les isolant par site
            max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 5,
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
        secure=os.getenv("COOKIE_SECURE", "true").lower() == "true",
        samesite="none", # none, permet en production d'envoyer le cookie cross-site
        partitioned=True, # permet de conserver des cookies tiers, mais en les isolant par site
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

import traceback

@app.post("/chats")
async def chats(data: CreateChat, current_user: Annotated[User, Depends(get_current_user)]):
    """
    Crée un nouveau chat pour l'utilisateur authentifié.

    Crée un nouveau chat associé à l'utilisateur authentifié. Si un message initial est fourni,
    il est envoyé au LLM et la réponse est ajoutée à l'historique des messages.

    Args:
        data: Données nécessaires à la création du chat.
        current_user: Utilisateur actuellement authentifié.

    Returns:
        Un message confirmant la création du chat.
        Le dictionnaire de données contient l'identifiant du chat créé.

    Raises:
        HTTPException: Si l'utilisateur n'est pas authentifié.
    """

    message = data.message.strip() if data.message else None

    print("************************************************")
    print("Message initial:", message)
    print("************************************************")

    messages = []
    if message:
        # archive le message de l'utilisateur
        messages.append({
            "date": datetime.now().isoformat(),
            "message": message,
            "type": "user"
        })

        # agent de qualification
        # appel LLM pour obtenir une demande structurée
        try:
            context = await classify_user_request(message)
            print("Contexte obtenu:", context.model_dump_json(indent=2))
        except Exception as e:
            print(f"Erreur lors de la classification de la demande utilisateur: {e}")
            traceback.print_exception(
                type(e),
                e,
                e.__traceback__,
                chain=True,
            )
            return ResponseApi(
                success=False,
                message="Impossible de déterminer le contexte de la demande",
                data={
                    "message": message,
                    "erreur": str(e)
                }
            )

        match context.intent:
            case Intent.NEWS_SEARCH | Intent.NEWS_QUESTION:
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
                    try:
                        response = await research(message)
                        print(f"RESPONSE", response)
                        messages.append({
                            "date": datetime.now().isoformat(),
                            "message": response,
                            "type": "assistant"
                        })
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du prompt au LLM: {e}")
                        return ResponseApi(
                            success=False,
                            message="Une erreur est survenue lors de l'appel au service IA",
                            data={
                                "message": message,
                                "erreur": str(e)
                            }
                        )
                # si les dates sont connues, on récupére les articles d'actualités
                else:
                    print(f"Du {start} au {end}")

                    try:
                        day_news = wn_receive_news(start, end, context.subject, context.category)
                        news_summary = wn_resume_news(day_news)
                        messages.append({
                            "date": datetime.now().isoformat(),
                            "message": news_summary,
                            "type": "system"
                        })
                    except Exception as e:
                        print(f"Erreur lors de la récupération des articles: {e}")
                        return ResponseApi(
                            success=False,
                            message="Une erreur est survenue lors de la récupération des articles",
                            data={
                                "message": message,
                                "erreur": str(e)
                            }
                        )

                    # synthétise les résultats
                    try:
                        response = await synthesize_news(messages, message)
                        print(f"RESPONSE", response)
                        messages.append({
                            "date": datetime.now().isoformat(),
                            "message": response,
                            "type": "assistant"
                        })
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du prompt au LLM: {e}")
                        return ResponseApi(
                            success=False,
                            message="Une erreur est survenue lors de l'appel au service IA",
                            data={
                                "message": message,
                                "erreur": str(e)
                            }
                        )

            case Intent.GENERAL_QUESTION:
                # interoge le LLM avec le message de l'utilisateur
                try:
                    response = await prompt_agent(message)
                    print(f"RESPONSE", response)
                    messages.append({
                        "date": datetime.now().isoformat(),
                        "message": response,
                        "type": "assistant"
                    })
                except Exception as e:
                    print(f"Erreur lors de l'envoi du prompt au LLM: {e}")
                    pass # si le LLM n'est pas dispo on conserve uniquement le message utilisateur

            case Intent.OUT_OF_SCOPE:
                response = "Je ne suis pas sûr de pouvoir répondre à cette question. Veuillez poser une question sur l'actualité."
                messages.append({
                    "date": datetime.now().isoformat(),
                    "message": response,
                    "type": "assistant"
                })

            case _:
                response = "Je ne parviens pas à déterminer le sens de votre question. Pouvez vous reformuler votre question ?"
                messages.append({
                    "date": datetime.now().isoformat(),
                    "message": response,
                    "type": "assistant"
                })

    else:
        response = "Comment puis je vous aider ? Posez moi une question sur l'actualité."
        messages.append({
            "date": datetime.now().isoformat(),
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
            data={
                "id": chat.id,
                "title": chat.title,
                "messages": chat.messages,
                "created_at": chat.created_at
            }
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
        messages = json.loads(chat.messages)
        message = data.message.strip()

        # archive le message de l'utilisateur
        messages.append({
            "date": datetime.now().isoformat(),
            "message": message,
            "type": "user"
        })


        # détermine la demande de l'utilisateur à partir du message et du contexte de la conversation
        try:
            decision = await manage_conversation(
                message=message,
                history=messages
            )
            
            print(decision.model_dump_json(indent=2))

            match decision.action:
                case ConversationAction.RESPOND if decision.response and decision.response.strip():
                    print(f"*******************************************")
                    print(f"RESPONSE", decision.response)
                    print(f"*******************************************")
                    response = decision.response
                    messages.append({
                        "date": datetime.now().isoformat(),
                        "message": decision.response,
                        "type": "assistant"
                    })
                case ConversationAction.RESEARCH:
                    # Lancer la recherche d'articles
                    print(f"*******************************************")
                    print(f"RESEARCH action triggered")
                    print(f"*******************************************")
                    response = ""
                    # agent de qualification
                    # appel LLM pour obtenir une demande structurée
                    try:
                        context = await prepare_research(message)
                        print("Contexte obtenu:", context.model_dump_json(indent=2))
                    except Exception as e:
                        raise handle_api_error(e, "Erreur lors de la classification de la demande utilisateur") from e

                    # si les dates ne sont pas spécifiées, on réalise une recherche via les outils de recherche d'actualités
                    if not context.start_date or not context.end_date:
                        # recherche des résultats
                        try:
                            response = await research(message)
                            messages.append({
                                "date": datetime.now().isoformat(),
                                "message": response,
                                "type": "assistant"
                            })
                        except Exception as e:
                            raise handle_api_error(e, "Erreur lors de la recherche des actualités") from e
                    # si les dates sont connues, on récupére les articles d'actualités
                    else:
                        print(f"Du {context.start_date} au {context.end_date}")

                        try:
                            day_news = wn_receive_news(context.start_date, context.end_date, context.subject)#, context.category)
                        except Exception as e:
                            raise handle_api_error(e, "Erreur lors de la récupération des actualités") from e

                        try:
                            news_summary = wn_resume_news(day_news)
                        except Exception as e:
                            raise handle_api_error(e, f"Erreur lors de la résumé des actualités du {context.start_date} au {context.end_date}") from e

                        messages.append({
                            "date": datetime.now().isoformat(),
                            "message": news_summary,
                            "type": "system"
                        })

                        # synthétise les résultats
                        try:
                            response = await synthesize_news(messages, message)
                            messages.append({
                                "date": datetime.now().isoformat(),
                                "message": response,
                                "type": "assistant"
                            })
                        except Exception as e:
                            raise handle_api_error(e, f"Erreur lors de la synthétisation des résultats du {context.start_date} au {context.end_date}") from e

                case ConversationAction.RESYNTHESIZE:
                    # Relancer l'agent de synthèse
                    print(f"*******************************************")
                    print(f"RESYNTHESIZE action triggered")
                    print(f"*******************************************")
                    # synthétise les résultats
                    try:
                        response = await synthesize_news(messages, message)
                        messages.append({
                            "date": datetime.now().isoformat(),
                            "message": response,
                            "type": "assistant"
                        })
                    except Exception as e:
                        raise handle_api_error(e, "Erreur lors de la synthétisation des résultats") from e
                    
                case ConversationAction.CLARIFY:
                    # La demande manque d'informations indispensables.
                    print(f"*******************************************")
                    print(f"CLARIFY action triggered")
                    print(f"*******************************************")
                    response = decision.complement if decision.complement and decision.complement.strip() else "Pouvez vous clarifier votre demande ?"
                    messages.append({
                        "date": datetime.now().isoformat(),
                        "message": response,
                        "type": "assistant"
                    })

                case ConversationAction.END:
                    print(f"*******************************************")
                    print(f"END action triggered")
                    print(f"*******************************************")
                    response = ""

                case _:
                    print(f"*******************************************")
                    print(f"Unknown action triggered")
                    print(f"*******************************************")
                    response = "Je ne parviens pas à déterminer le sens de votre question. Pouvez vous reformuler votre question ?"
                    messages.append({
                        "date": datetime.now().isoformat(),
                        "message": response,
                        "type": "assistant"
                    })
        
            print(f"RESPONSE", response)

        # l'erreur est connue est identifié par le programme
        except AppError as e:
            # debogage de l'erreur
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"Exception")
            e.print_debug()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            # réponse de l'API
            error = str(e)

            messages.append({
                "date": datetime.now().isoformat(),
                "message": error,
                "type": "error"
            })

            return ResponseApi(success=False, message="Erreur de traitement", data={
                "message": message,
                "response": error
            })

        # l'erreur n'est pas connue, on la traite comme une exception générique
        except Exception as e:
            # debogage de l'erreur
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"Exception non géré")
            print(str(e))
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            # réponse de l'API
            error = "Une erreur non gérée est survenue"

            messages.append({
                "date": datetime.now().isoformat(),
                "message": error,
                "type": "error"
            })

            return ResponseApi(success=False, message="Erreur de traitement", data={
                "message": message,
                "response": error
            })

        # on sauvegarde les messages du chat dans la base de données
        finally:
            try:
                chat.messages = json.dumps(messages)
                session.add(chat)
                session.commit()
            except Exception as e:
                return ResponseApi(success=False, message="Erreur lors de l'enregistrement des données", data={
                    "message": message,
                    "error": str(e)
                })

    return ResponseApi(success=True, message="Message ajouté avec succès", data={
        "message": message,
        "response": response
    })


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
            history=json.loads(chat.messages) if chat.messages else []
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
