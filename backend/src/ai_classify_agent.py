from datetime import date
from enum import Enum

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from ai import model
from datetime import date, timedelta


class Intent(str, Enum):
    """Intentions possibles d'une demande utilisateur."""

    NEWS_SEARCH = "news_search"
    NEWS_QUESTION = "news_question"
    GENERAL_QUESTION = "general_question"
    OUT_OF_SCOPE = "out_of_scope"


class Period(str, Enum):
    """Périodes relatives possibles."""

    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    CUSTOM = "custom"
    UNSPECIFIED = "unspecified"


class UserRequest(BaseModel):
    """Qualification structurée d'une demande utilisateur."""

    intent: Intent = Field(
        description="Intention principale de la demande."
    )

    subject: str | None = Field(
        default=None,
        description="Sujet principal de la demande.",
        min_length=16
    )

    category: str | None = Field(
        default=None,
        description="Catégorie principal de la demande."
    )

    period: Period = Field(
        default=Period.UNSPECIFIED,
        description="Période concernée par la demande."
    )

    period_start: date | None = Field(
        default=None,
        description="Date de début si une période personnalisée est demandée."
    )

    period_end: date | None = Field(
        default=None,
        description="Date de fin si une période personnalisée est demandée."
    )

    needs_news: bool = Field(
        description="Indique si une recherche d'articles est nécessaire."
    )

    requires_clarification: bool = Field(
        default=False,
        description="Indique si la demande nécessite une clarification."
    )

    clarification_question: str | None = Field(
        default=None,
        description="Question à poser si une clarification est nécessaire."
    )


qualification_agent = Agent(
    model,
    output_type=UserRequest,
    instructions="""
Tu es un agent chargé de qualifier les demandes des utilisateurs
d'une application de revue de presse.

Tu ne dois jamais répondre directement à la demande.
Tu dois uniquement déterminer sa nature et produire une qualification structurée.

INTENTIONS POSSIBLES :

1. news_search
L'utilisateur souhaite consulter des articles ou connaître les dernières
actualités sur un sujet.

Exemples :
- Quelles sont les dernières nouvelles sur l'intelligence artificielle ?
- Trouve-moi des articles sur Mistral.
- Que s'est-il passé cette semaine dans le secteur automobile ?

2. news_question
L'utilisateur pose une question portant sur un événement d'actualité,
une information récente ou un sujet nécessitant des articles pour y répondre.

Exemples :
- Pourquoi Nvidia a-t-il récemment investi dans l'IA ?
- Quelles sont les conséquences de la dernière annonce de Mistral ?

3. general_question
L'utilisateur pose une question générale qui ne nécessite pas de consulter
l'actualité.

Exemples :
- Comment fonctionne une intelligence artificielle ?
- Quelle est la différence entre Python et JavaScript ?

4. out_of_scope
La demande n'a aucun rapport avec la revue de presse ou les sujets
d'information que l'application est destinée à traiter.

GESTION DES PÉRIODES :

- today : aujourd'hui.
- yesterday : hier.
- last_7_days : les sept derniers jours.
- last_30_days : les trente derniers jours.
- custom : période explicitement définie par des dates.
- unspecified : aucune période identifiable.

Ne jamais inventer une période.
Ne pas utiliser custom sans dates identifiables.

RÈGLES :

- needs_news vaut true pour news_search et news_question.
- needs_news vaut false pour general_question et out_of_scope.
- subject doit identifier le sujet principal lorsque celui-ci est identifiable.
- category doit identifier la catégorie principale lorsque qu'elle est identifiable.
- Une demande ambiguë doit déclencher requires_clarification.
- clarification_question doit contenir une seule question précise.
- Ne pas demander de clarification si la demande est suffisamment claire.
- Une demande courte n'est pas nécessairement ambiguë.
- N'inventes pas de dates si elles ne sont pas explicitement spécifiées par l'utilisateur.
- Ne pas considérer une question comme hors sujet uniquement parce qu'elle ne contient pas le mot actualité ou information.
"""
)

async def classify_user_request(message: str) -> UserRequest:
    """
    Analyse une demande utilisateur et retourne son intention structurée.

    Args:
        message: Demande formulée par l'utilisateur.

    Returns:
        Qualification structurée de la demande.
    """

    result = await qualification_agent.run(message)

    return result.output


def period_to_dates(
    period: Period,
    period_start: date | None = None,
    period_end: date | None = None,
) -> tuple[date | None, date | None]:
    """
    Convertit une période en dates de début et de fin.

    Args:
        period: Période à convertir.
        period_start: Date de début personnalisée.
        period_end: Date de fin personnalisée.

    Returns:
        Tuple contenant la date de début et la date de fin.

    Raises:
        ValueError: Si les dates personnalisées sont invalides.
    """

    today = date.today()

    match period:
        case Period.TODAY:
            return today, today

        case Period.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday

        case Period.LAST_7_DAYS:
            return today - timedelta(days=6), today

        case Period.LAST_30_DAYS:
            return today - timedelta(days=29), today

        case Period.CUSTOM:
            if not period_start or not period_end:
                raise ValueError("Les dates personnalisées sont obligatoires.")

            if period_start > period_end:
                raise ValueError("La date de début doit précéder la date de fin.")

            return period_start, period_end

        case Period.UNSPECIFIED:
            return None, None

        case _:
            raise ValueError(f"Période inconnue : {period}")