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
        name: str = None,
        title: str = None,
        text: str = None,
        abs_oauth_connection_name: str = None,
        obo_connection_name: str = None,
        **kwargs,
    ):
        """
        Initializes a new instance of AuthHandler.

        Args:
            name: The name of the OAuth connection.
            auto: Whether to automatically start the OAuth flow.
            title: Title for the OAuth card.
            text: Text for the OAuth button.
        """
        self.name = name or kwargs.get("NAME")
        self.title = title or kwargs.get("TITLE")
        self.text = text or kwargs.get("TEXT")
        self.abs_oauth_connection_name = abs_oauth_connection_name or kwargs.get(
            "AZUREBOTOAUTHCONNECTIONNAME"
        )
        self.obo_connection_name = obo_connection_name or kwargs.get(
            "OBOCONNECTIONNAME"
        )
        logger.debug(
            f"AuthHandler initialized: name={self.name}, title={self.title}, text={self.text} abs_connection_name={self.abs_oauth_connection_name} obo_connection_name={self.obo_connection_name}"
        )


# # Type alias for authorization handlers dictionary
AuthorizationHandlers = Dict[str, AuthHandler]
