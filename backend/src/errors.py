
from dataclasses import dataclass
from typing import Any

import inspect
import traceback
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
    ):
        super().__init__(message)

        self.message = message
        self.details = details
        self.code = code
        self.function = function
        self.provider = provider
        self.status_code = status_code
        self.original_exception = original_exception

    def print_debug(self):
        print("AppError Debug Info:")
        print(f"Message    : {self.message}")
        print(f"Details    : {self.details}")
        print(f"Code       : {self.code}")
        print(f"Function   : {self.function}")
        print(f"Provider   : {self.provider}")
        print(f"Status Code: {self.status_code}")
        print(f"{type(self.original_exception).__name__}: {self.original_exception}")
            
        e = self.original_exception
        
        # Erreur HTTP remontée par Pydantic AI
        if isinstance(self.original_exception, ModelHTTPError):
            print("\n[LLM HTTP ERROR]")
            print(f"Type       : {type(e).__name__}")
            print(f"Message    : {e}")
            print(f"Status     : {e.status_code}")
            print(f"Body       : {e.body}")
            print(f"Code       : {e.provider_error_code}")
            print(f"Error type : {e.provider_error_type}")
            print(f"Headers    : {e.headers}")
            print(f"Retry after: {e.retry_after}")

        # Erreur API remontée par Pydantic AI
        elif isinstance(e, ModelAPIError):
            print("\n[LLM API ERROR]")
            print(f"Type    : {type(e).__name__}")
            print(f"Message : {e}")
            print(f"Body    : {getattr(e, 'body', None)}")

        if e.__cause__:
            print("\n[CAUSE ORIGINALE]")
            traceback.print_exception(e.__cause__)

    def __str__(self):
        return f"{self.message}\n\nDétails:{self.details}"



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

    # Erreur HTTP remontée par Pydantic AI
    if isinstance(e, ModelHTTPError):

        url = str(e.request.url)
        
        if "api.mistral.ai" in url:
            provider = "mistral"
        elif "api.worldnewsapi.com" in url:
            provider = "world news"

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
    
    # Erreur HTTPX, message de l'api world news ?
    elif isinstance(e, httpx.HTTPError):
        try:
            body = e.response.json()
            details = body.get("message", details)
        except Exception:
            pass
            
    # Erreur HTTPX
    elif isinstance(e, httpx.HTTPStatusError):

        url = str(e.request.url)
        
        if "api.mistral.ai" in url:
            provider = "mistral"
        elif "api.worldnewsapi.com" in url:
            provider = "world news"

        status_code = e.response.status_code

        try:
            body = e.response.json()
            details = body.get("message", details)
        except Exception:
            pass

        if status_code == 429:
            code = "RATE_LIMIT"
            details = "Le service est temporairement indisponible en raison d'une limite de requêtes."

        elif status_code in (401, 403):
            code = "AUTHENTICATION_ERROR"
            details = "L'authentification auprès du service a échoué."

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
    )
