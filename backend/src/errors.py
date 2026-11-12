
from dataclasses import dataclass
from typing import Any

import inspect
import httpx

from pydantic_ai.exceptions import ModelHTTPError, ModelAPIError, UnexpectedModelBehavior

@dataclass
class AppError(Exception):
    """Exception standardisée de l'application."""

    def __init__(
        self,
        message: str,
        details: str | None = None,
        code: str = "INTERNAL_ERROR",
        function: str | None = None,
        provider: str | None = None,
        status_code: int | None = None,
        original_exception: Exception | None = None,
        type: str | None = None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details
        self.code = code
        self.function = function
        self.provider = provider
        self.status_code = status_code
        self.original_exception = original_exception
        self.type = type

    def print_debug(self):
        try:
            print("AppError Debug Info:")
            print(f"Message    : {self.message}")
            print(f"Details    : {self.details}")
            print(f"Code       : {self.code}")
            print(f"Function   : {self.function}")
            print(f"Provider   : {self.provider}")
            print(f"Status Code: {self.status_code}")
            print(f"Type       : {self.type}")
            print(f"Origine    : {self.original_exception}")
                
            e = self.original_exception
            
            print("Exception détails:")
            print("----------------------------------------------")
            for name in dir(e):
                if not name.startswith("_"):
                    value = getattr(e, name, None)
                    if not callable(value):
                        print(f"{name} = {value}")
            print("----------------------------------------------")
        except Exception as ex:
            print(f"Erreur lors de l'affichage des détails de l'exception: {ex}")

    def __str__(self):
        return f"{self.details or self.message}"


def handle_api_error(e: Exception, message: str | None = None) -> AppError:
    """
    Convertit une exception en AppError.
    AppError est utilisé pour centraliser la gestion des erreurs dans l'application et proposer un format de message commun
    Args:
        e: L'exception à convertir.
        message: Message optionnel à afficher pour l'erreur.
    Returns:
        Une instance de AppError représentant l'erreur.
    """

    frame = inspect.currentframe()

    try:
        caller = frame.f_back
        function = caller.f_code.co_name if caller else "unknown"
    finally:
        del frame

    provider = "unknown"
    status_code = None
    code = "API_ERROR"

    if message is None:
        message = "Une erreur est survenue lors du traitement de la demande"

    details = None

    # Problème de connexion
    if isinstance(e, AppError):
        return e

    # Erreur HTTP remontée par Pydantic AI
    elif isinstance(e, ModelHTTPError):
        status_code = e.status_code

        body = e.body

        if isinstance(body, dict):
            details = body.get("message") or details
            code = body.get("code") or code
        elif body:
            details = str(body)

        if status_code == 429:
            code = "RATE_LIMIT"
            details = "Le service est temporairement indisponible en raison d'une limite de requêtes."

        elif status_code in (401, 403):
            code = "AUTHENTICATION_ERROR"
            details = "L'authentification auprès du service a échoué."

    # Erreur API remontée par Pydantic AI
    elif isinstance(e, ModelAPIError):
        provider = "mistral"
        status_code = None
        details = str(e)

    # Erreur remontée par un outil
    elif isinstance(e, UnexpectedModelBehavior):
        return AppError(
            message="Une erreur est survenue pendant l'exécution d'un outil.",
            code="TOOL_EXECUTION_ERROR",
            original_exception=e,
        )
    
    # Erreur HTTPX
    elif isinstance(e, httpx.HTTPStatusError):
        url = str(e.request.url)
        print("url", url)
        
        if "api.mistral.ai" in url:
            provider = "Mistral"
        elif "generativelanguage.googleapis.com" in url:
            provider = "Gemini"
        elif "api.worldnewsapi.com" in url:
            provider = "WorldNews"

        status_code = e.response.status_code

        if status_code == 429:
            code = "RATE_LIMIT"
            details = f"Le service {provider} est temporairement indisponible en raison d'une limite de requêtes."

        elif status_code == 402:
            code = "PAYMENT_REQUIRED"
            details = f"Le service {provider} a refusé la requête : le quota disponible est épuisé ou le forfait ne permet pas cette opération."

        elif status_code in (401, 403):
            code = "AUTHENTICATION_ERROR"
            details = f"L'authentification auprès du service {provider} a échoué."

    # Erreur HTTPX, message de l'api world news ?
    elif isinstance(e, httpx.HTTPError):
        try:
            body = e.response.json()
            details = body.get("message", details)
        except Exception:
            pass
            
    # Timeout
    elif isinstance(e, httpx.TimeoutException):
        code = "API_TIMEOUT"
        details = "Le service n'a pas répondu dans le délai imparti."

    # Problème de connexion
    elif isinstance(e, httpx.RequestError):
        code = "API_CONNECTION_ERROR"
        details = "Impossible de contacter le service distant."

    return AppError(
        message=message,
        details=details,
        code=code,
        function=function,
        provider=provider,
        status_code=status_code,
        original_exception=e,
        type=f"{type(e).__module__}.{type(e).__qualname__}"
    )
