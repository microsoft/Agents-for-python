"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import logging
import warnings

logger = logging.getLogger(__name__)


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
        name: str = "",
        title: str = "",
        text: str = "",
        abs_oauth_connection_name: str = "",
        obo_connection_name: str = "",
        auth_type: str = "",
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
        self.auth_type = auth_type or kwargs.get("type", "UserAuthorization")
        self.auth_type = self.auth_type.lower()
        if scopes:
            self.scopes = list(scopes)
        else:
            self.scopes = AuthHandlerSettings._format_scopes(kwargs.get("scopes", ""))
        self._alt_blueprint_name = kwargs.get("alt_blueprint_name", None)
        self._kwargs = kwargs

    @property
    def kwargs(self) -> dict:
        return dict(self._kwargs)

    @staticmethod
    def _format_scopes(scopes: str) -> list[str]:
        lst = scopes.strip().split(" ")
        return [s for s in lst if s]

    @staticmethod
    def _from_settings(settings: dict):
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
        return AuthHandlerSettings(**settings)

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
            "abs_oauth_connection_name": self.abs_oauth_connection_name,
            "obo_connection_name": self.obo_connection_name,
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
