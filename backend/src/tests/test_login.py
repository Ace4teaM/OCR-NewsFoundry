
"""Tests de la route d'authentification /login."""

import os
from types import SimpleNamespace

# Définir les variables avant l'import de main.
os.environ.setdefault("ALLOW_ORIGINS", "http://localhost:3000")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("MISTRAL_API_KEY", "unused-key")
os.environ.setdefault("WORLDNEWS_API_KEY", "unused-key")
os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost:5432/newsfoundry")
os.environ["COOKIE_SECURE"] = "false"

import bcrypt
import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR))

import main


class FakeResult:
    """Simule le résultat d'une requête SQLModel."""

    def __init__(self, user):
        self.user = user

    def first(self):
        return self.user


class FakeSession:
    """Simule une session de base de données."""

    user = None
    chat = None

    def __init__(self, engine):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def exec(self, statement):
        return FakeResult(self.user)

    def get(self, model, entity_id):
        if model is main.Chat and self.chat and self.chat.id == entity_id:
            return self.chat
        if model is main.User and self.user and self.user.id == entity_id:
            return self.user
        return None


# Simule un client HTTP pour appeler l'API FastAPI
@pytest.fixture
def client(monkeypatch):
    """Prépare un client HTTP et une base simulée pour chaque test."""

    # remplace la session existantes par une session simulée
    monkeypatch.setattr(main, "Session", FakeSession)

    # Réinitialise pour chaque test.
    FakeSession.user = None
    FakeSession.chat = None

    # retourne un client Http de test
    return TestClient(main.app)

# Prépare un utilisateur fictif
@pytest.fixture
def user():
    """Construit un utilisateur de test avec un véritable hash bcrypt."""

    password = "MotDePasse-Test-123"

    return SimpleNamespace(
        id=1,
        email="user@example.com",
        hashed_password=bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8"),
    )


def test_login_with_valid_credentials(client, user, monkeypatch): # monkeypatch Fixture intégrée à pytest
    """Un utilisateur valide reçoit un cookie JWT HttpOnly."""

    FakeSession.user = user
    monkeypatch.setenv("COOKIE_SECURE", "false")

    response = client.post(
        "/login",
        json={
            "email": user.email,
            "password": "MotDePasse-Test-123",
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["message"] == "Connexion réussie"

    cookie = response.cookies.get("access_token")
    assert cookie is not None

    # Vérifie les attributs de sécurité du cookie.
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "path=/" in set_cookie

    # Le cookie contient un JWT valide pour l'utilisateur connecté.
    payload = main.jwt.decode(
        cookie,
        main.JWT_SECRET_KEY,
        algorithms=[main.JWT_ALGORITHM],
    )
    assert payload["sub"] == str(user.id)


def test_login_with_unknown_user(client):
    """Un utilisateur inconnu ne peut pas obtenir de cookie JWT."""

    FakeSession.user = None

    response = client.post(
        "/login",
        json={
            "email": "unknown@example.com",
            "password": "MotDePasse-Test-123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Email ou mot de passe incorrect"
    )
    assert "access_token" not in response.cookies
    assert "set-cookie" not in response.headers


def test_login_with_wrong_password(client, user):
    """Un mot de passe incorrect ne permet pas de se connecter."""

    FakeSession.user = user

    response = client.post(
        "/login",
        json={
            "email": user.email,
            "password": "MauvaisMotDePasse",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Email ou mot de passe incorrect"
    )
    assert "access_token" not in response.cookies
    assert "set-cookie" not in response.headers

    
def test_user_cannot_access_another_users_chat(client, user):
    """Un utilisateur ne peut pas consulter le chat d'un autre utilisateur."""

    # L'utilisateur connecté possède l'identifiant 1.
    FakeSession.user = user

    # Le chat demandé appartient à l'utilisateur 2.
    FakeSession.chat = SimpleNamespace(
        id=42,
        user_id=2,
        title="Discussion privée",
        created_at="2026-10-29",
        messages="[]",
    )

    # Authentification de l'utilisateur 1.
    login_response = client.post(
        "/login",
        json={
            "email": user.email,
            "password": "MotDePasse-Test-123",
        },
    )

    assert login_response.status_code == 200

    # Tentative d'accès au chat de l'utilisateur 2.
    response = client.get("/chats/42")

    assert response.status_code == 401