import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated
from database import init_db, engine
from fastapi import FastAPI, HTTPException, status, Response, Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
import bcrypt
import uvicorn
from models import User
import bcrypt
import jwt

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

@dataclass
class ResponseApi():
    """Données d'une réponse structurée de l'API"""
    success: bool
    message: str



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
            samesite="lax",
            max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

        return ResponseApi(success=True, message="Connexion réussie")


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
        samesite="lax",
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
    return {
        "id": current_user.id,
        "email": current_user.email,
    }



if __name__ == "__main__":
    init_db()

    uvicorn.run(app, host="0.0.0.0", port=8000)
