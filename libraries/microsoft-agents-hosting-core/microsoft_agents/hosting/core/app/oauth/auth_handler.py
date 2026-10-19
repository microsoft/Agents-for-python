"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import logging
import warnings

logger = logging.getLogger(__name__)

_BASE_KEYS = [
    "name",
    "title",
    "text",
    "azurebotoauthconnectionname",
    "oboconnectionname",
    "type",
    "scopes",
    "alt_blueprint_name",
]


# name due to compat.
# see AuthorizationHandler for a class that does work.
class AuthHandlerSettings:
    """
    Interface defining an authorization handler for OAuth flows.
    """

    name: str
    title: str
    text: str
    abs_oauth_connection_name: str
    obo_connection_name: str
    auth_type: str
    scopes: list[str]

    def __init__(
        self,
        name: str | None = None,
        title: str | None = None,
        text: str | None = None,
        abs_oauth_connection_name: str | None = None,
        obo_connection_name: str | None = None,
        auth_type: str | None = None,
        scopes: list[str] | None = None,
        **kwargs,
    ):
        """
        Initializes a new instance of AuthHandlerSettings.

        :param name: The name of the handler. This is how it is accessed programatically
            in this library.
        :type name: str
        :param title: Title for the OAuth card.
        :type title: str
        :param text: Text for the OAuth button.
        :type text: str
        :param abs_oauth_connection_name: The name of the Azure Bot Service OAuth connection.
        :type abs_oauth_connection_name: str
        :param obo_connection_name: The name of the On-Behalf-Of connection.
        :type obo_connection_name: str
        :param auth_type: The authorization variant used. This is likely to change in the future
            to accept a class that implements AuthorizationVariant.
        :type auth_type: str
        """

        base, extras = AuthHandlerSettings._resolve(
            {
                "name": name,
                "title": title,
                "text": text,
                "azurebotoauthconnectionname": abs_oauth_connection_name,
                "oboconnectionname": obo_connection_name,
                "type": auth_type,
                "scopes": scopes,
                "alt_blueprint_name": kwargs.get("alt_blueprint_name", None),
            },
            kwargs,
        )

        self.name = base.get("name", "")
        self.title = base.get("title", "")
        self.text = base.get("text", "")
        self.abs_oauth_connection_name = base.get("azurebotoauthconnectionname", "")
        self.obo_connection_name = base.get("oboconnectionname", "")
        self.auth_type = base.get("type", "UserAuthorization").lower()
        self.scopes = AuthHandlerSettings._format_scopes(base.get("scopes", ""))
        self._alt_blueprint_name = base.get("alt_blueprint_name", None)
        self._kwargs = extras

    @staticmethod
    def _resolve(settings: dict, other: dict) -> tuple[dict, dict]:

        settings = {k.lower(): v for k, v in settings.items()}
        other = {k.lower(): v for k, v in other.items()}

        if "abs_oauth_connection_name" in settings:
            settings["azurebotoauthconnectionname"] = settings.pop(
                "abs_oauth_connection_name"
            )
        if "obo_connection_name" in settings:
            settings["oboconnectionname"] = settings.pop("obo_connection_name")
        if "auth_type" in settings:
            settings["type"] = settings.pop("auth_type")

        if "abs_oauth_connection_name" in other:
            other["azurebotoauthconnectionname"] = other.pop(
                "abs_oauth_connection_name"
            )
        if "obo_connection_name" in other:
            other["oboconnectionname"] = other.pop("obo_connection_name")
        if "auth_type" in other:
            other["type"] = other.pop("auth_type")

        base = {
            "name": settings.get("name") or other.get("name", ""),
            "title": settings.get("title") or other.get("title", ""),
            "text": settings.get("text") or other.get("text", ""),
            "azurebotoauthconnectionname": settings.get("azurebotoauthconnectionname")
            or other.get("azurebotoauthconnectionname", ""),
            "oboconnectionname": settings.get("oboconnectionname")
            or other.get("oboconnectionname", ""),
            "type": settings.get("type") or other.get("type", "UserAuthorization"),
            "scopes": settings.get("scopes") or other.get("scopes", ""),
            "alt_blueprint_name": settings.get("alt_blueprint_name")
            or other.get("alt_blueprint_name", None),
        }
        base_keys = base.keys()

        extras_base = {k: v for k, v in settings.items() if k not in base_keys}
        extras_other = {k: v for k, v in other.items() if k not in base_keys}
        extras = {**extras_other, **extras_base}
        return base, extras

    @property
    def kwargs(self) -> dict:
        return dict(self._kwargs)

    @staticmethod
    def _format_scopes(scopes: str | list[str]) -> list[str]:
        if isinstance(scopes, str):
            lst = scopes.strip().split(" ")
            return [s for s in lst if s]
        elif isinstance(scopes, list):
            return list(scopes)
        else:
            return []

    @staticmethod
    def _from_settings(settings: dict, **kwargs):
        """
        Creates an AuthHandlerSettings instance from a settings dictionary.

        :param settings: The settings dictionary containing configuration for the AuthHandlerSettings.
        :type settings: dict
        :return: An instance of AuthHandlerSettings configured with the provided settings.
        :rtype: AuthHandlerSettings
        """
        if not settings:
            raise ValueError(
                "Settings dictionary is required to create AuthHandlerSettings"
            )

        base, extras = AuthHandlerSettings._resolve(settings, kwargs)

        return AuthHandlerSettings(**base, **extras)

    def _to_dict(self) -> dict:
        """
        Converts the AuthHandlerSettings instance to a dictionary.

        :return: A dictionary representation of the AuthHandlerSettings instance.
        :rtype: dict
        """
        base = {
            "name": self.name,
            "title": self.title,
            "text": self.text,
            "azurebotoauthconnectionname": self.abs_oauth_connection_name,
            "oboconnectionname": self.obo_connection_name,
            "type": self.auth_type,
            "scopes": self.scopes,
            "alt_blueprint_name": self._alt_blueprint_name,
        }
        return {**self._kwargs, **base}


class AuthHandler(AuthHandlerSettings):
    """Deprecated. Use AuthHandlerSettings instead."""

    def __init__(self, *args, **kwargs):
        """Initialize the deprecated AuthHandler class."""
        warnings.warn(
            "AuthHandler is deprecated. Please use AuthHandlerSettings instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
