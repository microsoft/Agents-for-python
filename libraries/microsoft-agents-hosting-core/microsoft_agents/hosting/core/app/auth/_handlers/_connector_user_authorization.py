# """
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# """

# from abc import ABC
# from typing import Optional
# import logging

# from microsoft_agents.activity import TokenResponse

# from ....turn_context import TurnContext
# from ....storage import Storage
# from ....authorization import Connections
# from ..auth_handler import AuthHandler
# from .._sign_in_response import _SignInResponse

# from ._authorization_handler import _AuthorizationHandler

# class _ConnectorUserAuthorizationHandler(_AuthorizationHandler):
#     """Authorization handler for connector user OAuth flow."""

#     # def get_obo_settings(self) -> dict:
#     #     """Get On-Behalf-Of settings for the auth handler.

#     #     :return: The OBO settings dictionary.
#     #     :rtype: dict
#     #     """
#     #     return self._

#     async def _sign_in(
#         self, context: TurnContext, scopes: Optional[list[str]] = None
#     ) -> _SignInResponse:
#         raise NotImplementedError(
#             "_sign_in is not implemented for Connector User Authorization."
#         )


#     async def get_refreshed_token(
#         self,
#         context: TurnContext,
#         exchange_connection: Optional[str] = None,
#         exchange_scopes: Optional[list[str]] = None,
#     ) -> TokenResponse:
        
#         token_response = self.create_token_response(context)

#     async def _sign_out(self, context: TurnContext) -> None:
#         raise NotImplementedError
    
#     def create_token_response(self, context: TurnContext) -> TokenResponse:

#         if _ConnectorUserAuthorizationHandler._is_case_sensitive_claims_identity(
#             context.turn_state.get("claims_identity")
#         ):
#             token_response = TokenResponse(token=identity.security_token.unsafe_to_str())

#             try:
#                 jwt_token = 

#     @staticmethod
#     def _is_case_sensitive_claims_identity(identity: ClaimsIdentity) -> bool:
#         return False