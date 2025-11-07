"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# name due to compat.
# see AuthorizationHandler for a class that does work.
class AuthHandler:
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
        scopes: Optional[list[str]] = None,
        **kwargs,
    ):
        """
        Initializes a new instance of AuthHandler.

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
        self.name = name or kwargs.get("NAME", "")
        self.title = title or kwargs.get("TITLE", "")
        self.text = text or kwargs.get("TEXT", "")
        self.abs_oauth_connection_name = abs_oauth_connection_name or kwargs.get(
            "AZUREBOTOAUTHCONNECTIONNAME", ""
        )
        self.obo_connection_name = obo_connection_name or kwargs.get(
            "OBOCONNECTIONNAME", ""
        )
        self.auth_type = auth_type or kwargs.get("TYPE", "UserAuthorization")
        self.auth_type = self.auth_type.lower()
        if scopes:
            self.scopes = list(scopes)
        else:
            self.scopes = AuthHandler._format_scopes(kwargs.get("SCOPES", ""))
        self._alt_blueprint_name = kwargs.get("ALT_BLUEPRINT_NAME", None)

    @staticmethod
    def _format_scopes(scopes: str) -> list[str]:
        lst = scopes.strip().split(" ")
        return [s for s in lst if s]

    @staticmethod
    def _from_settings(settings: dict):
        """
        Creates an AuthHandler instance from a settings dictionary.

        :param settings: The settings dictionary containing configuration for the AuthHandler.
        :type settings: dict
        :return: An instance of AuthHandler configured with the provided settings.
        :rtype: AuthHandler
        """
        if not settings:
            raise ValueError("Settings dictionary is required to create AuthHandler")

        return AuthHandler(
            name=settings.get("NAME", ""),
            title=settings.get("TITLE", ""),
            text=settings.get("TEXT", ""),
            abs_oauth_connection_name=settings.get("AZUREBOTOAUTHCONNECTIONNAME", ""),
            obo_connection_name=settings.get("OBOCONNECTIONNAME", ""),
            auth_type=settings.get("TYPE", ""),
            scopes=AuthHandler._format_scopes(settings.get("SCOPES", "")),
        )
