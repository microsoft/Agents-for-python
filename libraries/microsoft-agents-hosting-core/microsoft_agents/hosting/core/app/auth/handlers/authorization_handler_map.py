from .authorization_handler import AuthorizationVariant
from .agentic_authorization import AgenticAuthorization
from .user_authorization import UserAuthorization

AUTHORIZATION_TYPE_MAP: dict[str, type[AuthorizationVariant]] = {
    UserAuthorization.__name__.lower(): UserAuthorization,
    AgenticAuthorization.__name__.lower(): AgenticAuthorization,
}
