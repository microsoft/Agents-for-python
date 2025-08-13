import logging
from typing import Optional, Callable

from .sign_in_storage import SignInStorage, SignInHandlerState, SignInHandlerStateStatus, FlowState

logger = logging.getLogger(__name__)

ms_agents_logger = logging.getLogger("microsoft.agents")
handler_formatter = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"))
ms_agents_logger.addHandler(console_handler)
ms_agents_logger.setLevel(logging.INFO)



class SignInContext:

    logger = logging.getLogger(f"{__name__}.SignInContext") # robrandao: TODO get logger with config

    def __init__(self,
                 storage: SignInStorage,
                 auth_handlers: AuthHandlers,
                 context: TurnContext,
                 handler_id: str = "",
                 is_started_from_route: bool = True):
        
        if not is_started_from_route and not handler_id:
            raise ValueError("handler_id must be provided when is_started_from_route is False.")

        if not hasattr(context, "activity"):  # robrandao: TODO -> see extra condition in JS code
            raise ValueError("context must have an activity property.")
        
        # robrandao: TODO -> is this necessary here, or can we do this outside? Can we make the storage outside too?
        # if self.is_started_from_route:

    # robrandao: TODO type signature
    def on_success(self, handler: Callable) -> None:
        self.__on_success_handler = handler

    def on_failure(self, handler: Callable) -> None:
        self.__on_failure_handler = handler

    async def get_token(self) -> Optional[TokenResponse]:

        if not await self.load_handler():
            return TokenResponse()
        
        self.logger.info("Getting token from user token service.")
        return self.__auth_handler.flow.get_token(self.context)
    
    async def exchange_token(self, scopes: list[str]) -> TokenResponse:
        if not await self.load_handler():
            return TokenResponse()
        
        self.logger.info("Exchanging token from user token service.")
        token_response = await self.__auth_handler.flow.get_token(self.context)
        if self.is_exchangeable(token_response.token):
            return await self.handle_obo(token_response.token, scopes)
        return token_response
    
    async def sign_out(self) -> None:
        if not await self.load_handler():
            return
        
        self.logger.info("Signing out from the authorization flow.")
        if self.is_started_from_route:
            await self.storage.handler_delete(self.handler.id)
        return self.__auth_handler.flow.sign_out(self.context)
    
    async def get_token(self) -> Optional[TokenResponse]:
        if not await self.load_handler():
            return TokenResponse()
        
        self.logger.debug("Processing authorization flow.")
        self.logger.debug(f"Uses Storage state: {self.is_started_from_route}")
        self.logger.debug("Current sign-in state:", self.handler)
        
        token_response = await self.handler.status(
            {} # robrandao: TODO
        )

        self.logger.debug("OAuth flow result: %s", { token: token_response.get(token), state: self.handler})
        return token_response
    
    DEFAULT_STATES: dict[SignInHandlerStateStatus, FlowState] = {
        "begin": lambda: { id: self.handler_id, status: status}
    }

    def __set_status(status: SignInHandlerStateStatus) -> None:

        # robrandao: TODO - type
        state_builder: dict[str, Callable] = {
            SignInHandlerStateStatus.BEGIN: (lambda: {
                "id": self.handler_id,
                "status": SignInHandlerStateStatus.BEGIN
            }),
            SignInHandlerStateStatus.CONTINUE: (lambda self: {
                **self.handler,
                "status": SignInHandlerStateStatus.CONTINUE,
                "state": self.flow_state
                "continuation_activity": self.context.activity
            }),
            SignInHandlerStatus.SUCCESS: (lambda: {
                **self.handler,
                "status": SignInHandlerStateStatus.SUCCESS,
                "state": None
            }),
            SignInHandlerStateStatus.FAILURE: (lambda: {
                **self.handler,
                "status": SignInHandlerStateStatus.FAILURE,
                "state": self.flow_state
            })
        }

        self.__handler = state_builder[status]()
        return self.__handler # robrandao: TODO ???
    
    async def __load_handler(self) -> bool:
        if self.is_started_from_route:
            if self.handler_id:
                self.__handler = await self.storage.handler_get(self.handler_id)
            else:
                self.__handler = await self.storage.handler_active()
        
        if not self.__handler:
            # robrandao: TODO renaming?
            self.__handler = self.__set_status(SignInHandlerStateStatus.NOT_STARTED, None)

        if not self.handler.id:
            return False
    
        self.__auth_handler = self.get_auth_handler_or_throw(self.handler.id)

        # robrandao: TODO
        if not self.is_started_from_route and self.flow_state.flow_started:
            self.set_status(SignInHandlerStateStatus.SUCCESS)
            self.logger.debug("OAuth flow success, using existing state.")
            return True
        
        if self.handler.status == SignInHandlerStateStatus.BEGIN:
            self.logger.debug("No active flow state, starting a new OAuth flow.")
            await self.__auth_handler.flow.sign_out(self.context)
        else:
            await self.__auth_handler.flow.set_flow_state(self.context, self.handler.state or FlowState()) # robrandao: TODO
        
        return True
    
    async def begin(self) -> None:
        self.logger.debug("Beginning OAuth flow.")
        await self.__auth_handler.flow.begin_flow(self.context)
        self.logger.debug("OAuth flow started, waiting on continuation...")
        self.__set_status(SignInHandlerStateStatus.CONTINUE)
        if self.is_started_from_route:
            await self.storage.handler_set(self.handler)

    async def continue(self) -> Optional[TokenResponse]:

        self.logger.debug("Continuing OAuth flow.")
    
        token_response = await self.__auth_handler.flow.continue_flow(self.context)
        if token_response.token:
            self.set_status(SignInHandlerStateStatus.SUCCESS)
            self.logger.debug("OAuth flow success.")
            if self.is_started_from_route:
                await self.storage.handler_set(self.handler)
            if self.__on_success_handler:
                await self.__on_success_handler()

        else:
            await self.failure()

        return token_response

    async def success(self) -> Optional[TokenResponse]:
        token_response = await self.__auth_handler.flow.get_token(self.context)
        # robrandao: TODO -> JS always strips() the token?
        if self.is_started_from_route and token_response.token:
            self.logger.debug("OAuth flow success, retrieving token.")
            return token_response
        else:
            self.logger.debug("OAuth flow token not available, waiting on continuation...")
            return self.continue()

    async def failure(self) -> None:
        self.__set_status(SignInHandlerStateStatus.FAILURE)

        # TODO

    async def __is_exchangeable(self, token: Optional[str]) -> bool:
        if not token or not isinstance(token, str): # robrandao: TODO ???
            return False
        
        payload = JwtToken.parse(token).payload # robrandao: TODO
        return payload.aud.index("api://") == 0
    
    async def __handle_obo(self, token: str, scopes: list[str]) -> TokenResponse:
        msal_token_provider = MsalTokenProvider()

        auth_config = self.context.adapter.auth_config
        if self.__auth_handler.cnx_prefix:
            auth_config = load_auth_config_from_env(self.__auth_handler.cnx_prefix)

        new_token = await msal_token_provider.get_on_behalf_of_token(auth_config, scopes, token)
        return TokenResponse(token)
    
    async def __get_auth_handler_or_throw(handler_id: str) -> AuthHandler:
        # robrandao: TODO
        pass