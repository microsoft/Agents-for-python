# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AuthHandler:
    """
    Interface defining an authorization handler for OAuth flows.
    """

    def __init__(
        self,
        name: str = "",
        title: str = "",
        text: str = "",
        abs_oauth_connection_name: str = "",
        obo_connection_name: str = "",
        auth_type: str = "",
        scopes: list[str] = None
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
        self.auth_type = auth_type or kwargs.get("TYPE", "")
        self.auth_type = self.auth_type.lower()
        self.scopes = list(scopes) or kwargs.get("SCOPES", [])


# # Type alias for authorization handlers dictionary
AuthorizationHandlers = Dict[str, AuthHandler]
