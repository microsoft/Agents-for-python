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
    kwargs: dict

    def __init__(
        self,
<<<<<<< HEAD
        name: str = "",
        title: str = "",
        text: str = "",
        abs_oauth_connection_name: str = "",
        obo_connection_name: str = "",
        auth_type: str = "",
=======
        name: str | None = None,
        title: str | None = None,
        text: str | None = None,
        abs_oauth_connection_name: str | None = None,
        obo_connection_name: str | None = None,
        auth_type: str | None = None,
>>>>>>> d8aa60a1e3d64641e35231787781b0d3ad06dfff
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
        :param scopes: List of scopes to request during sign-in.
        :type scopes: list[str] | None
        :param kwargs: Additional keyword arguments for the OAuth handler.
            _alt_blueprint_name: Alternative blueprint name for the OAuth handler.
        :type kwargs: dict
        """

        kwargs = {k.lower(): v for k, v in kwargs.items()}

        self.name = name or kwargs.get("name", "")
        self.title = title or kwargs.get("title", "")
        self.text = text or kwargs.get("text", "")
        self.abs_oauth_connection_name = abs_oauth_connection_name or kwargs.get(
            "azurebotoauthconnectionname", ""
        )
        self.obo_connection_name = obo_connection_name or kwargs.get(
            "oboconnectionname", ""
        )
        self.auth_type = (auth_type or kwargs.get("type", "UserAuthorization")).lower()
        self.scopes = AuthHandlerSettings._format_scopes(
            scopes or kwargs.get("scopes", "")
        )
        self._alt_blueprint_name = kwargs.get("alt_blueprint_name", None)

        self._kwargs = {k: v for k, v in kwargs.items() if k not in _BASE_KEYS}

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
<<<<<<< HEAD
            self.scopes = AuthHandlerSettings._format_scopes(kwargs.get("SCOPES", ""))
        self._alt_blueprint_name = kwargs.get("ALT_BLUEPRINT_NAME", None)
        self.kwargs = dict(kwargs)
=======
            return []
>>>>>>> d8aa60a1e3d64641e35231787781b0d3ad06dfff

    def _to_dict(self) -> dict:
        """
<<<<<<< HEAD
        Creates an AuthHandlerSettings instance from a settings dictionary.

        :param settings: The settings dictionary containing configuration for the AuthHandlerSettings.
        :type settings: dict
        :return: An instance of AuthHandlerSettings configured with the provided settings.
        :rtype: AuthHandlerSettings
        """
        if not settings:
            raise ValueError("Settings dictionary is required to create AuthHandlerSettings")

        return AuthHandlerSettings(
            name=settings.get("NAME", ""),
            title=settings.get("TITLE", ""),
            text=settings.get("TEXT", ""),
            abs_oauth_connection_name=settings.get("AZUREBOTOAUTHCONNECTIONNAME", ""),
            obo_connection_name=settings.get("OBOCONNECTIONNAME", ""),
            auth_type=settings.get("TYPE", ""),
            scopes=AuthHandlerSettings._format_scopes(settings.get("SCOPES", "")),
        )

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
=======
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
>>>>>>> d8aa60a1e3d64641e35231787781b0d3ad06dfff
