"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations
import logging
from copy import copy
from functools import partial

import re
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Pattern,
    TypeVar,
    Union,
    cast,
)

from microsoft.agents.hosting.core.authorization import Connections

from microsoft.agents.hosting.core import Agent, TurnContext
from microsoft.agents.activity import (
    Activity,
    ActivityTypes,
    ConversationUpdateTypes,
    MessageReactionTypes,
    MessageUpdateTypes,
    InvokeResponse,
)

from .app_error import ApplicationError
from .app_options import ApplicationOptions

# from .auth import AuthManager, OAuth, OAuthOptions
from .route import Route, RouteHandler
from .state import TurnState
from ..channel_service_adapter import ChannelServiceAdapter
from .oauth import Authorization, SignInState
from .typing_indicator import TypingIndicator

logger = logging.getLogger(__name__)

StateT = TypeVar("StateT", bound=TurnState)
IN_SIGN_IN_KEY = "__InSignInFlow__"


class AgentApplication(Agent, Generic[StateT]):
    """
    AgentApplication class for routing and processing incoming requests.

    The AgentApplication object replaces the traditional ActivityHandler that
    a bot would use. It supports a simpler fluent style of authoring bots
    versus the inheritance based approach used by the ActivityHandler class.

    Additionally, it has built-in support for calling into the SDK's AI system
    and can be used to create bots that leverage Large Language Models (LLM)
    and other AI capabilities.
    """

    typing: TypingIndicator

    _options: ApplicationOptions
    _adapter: Optional[ChannelServiceAdapter] = None
    _auth: Optional[Authorization] = None
    _internal_before_turn: List[Callable[[TurnContext, StateT], Awaitable[bool]]] = []
    _internal_after_turn: List[Callable[[TurnContext, StateT], Awaitable[bool]]] = []
    _routes: List[Route[StateT]] = []
    _error: Optional[Callable[[TurnContext, Exception], Awaitable[None]]] = None
    _turn_state_factory: Optional[Callable[[TurnContext], StateT]] = None

    def __init__(
        self,
        options: ApplicationOptions = None,
        *,
        connection_manager: Connections = None,
        authorization: Authorization = None,
        **kwargs,
    ) -> None:
        """
        Creates a new AgentApplication instance.
        """
        self.typing = TypingIndicator()
        self._routes = []

        configuration = kwargs

        logger.debug(f"Initializing AgentApplication with options: {options}")
        logger.debug(
            f"Initializing AgentApplication with configuration: {configuration}"
        )

        if not options:
            # TODO: consolidate configuration story
            # Take the options from the kwargs and create an ApplicationOptions instance
            option_kwargs = dict(
                filter(
                    lambda x: x[0] in ApplicationOptions.__dataclass_fields__,
                    kwargs.items(),
                )
            )
            options = ApplicationOptions(**option_kwargs)

        self._options = options

        if not self._options.storage:
            logger.error(
                "ApplicationOptions.storage is required and was not configured.",
                stack_info=True,
            )
            raise ApplicationError(
                """
                The `ApplicationOptions.storage` property is required and was not configured.
                """
            )

        if options.long_running_messages and (
            not options.adapter or not options.bot_app_id
        ):
            logger.error(
                "ApplicationOptions.long_running_messages requires an adapter and bot_app_id.",
                stack_info=True,
            )
            raise ApplicationError(
                """
                The `ApplicationOptions.long_running_messages` property is unavailable because 
                no adapter or `bot_app_id` was configured.
                """
            )

        if options.adapter:
            self._adapter = options.adapter

        self._turn_state_factory = (
            options.turn_state_factory
            or kwargs.get("turn_state_factory", None)
            or partial(TurnState.with_storage, self._options.storage)
        )

        # TODO: decide how to initialize the Authorization (params vs options vs kwargs)
        if authorization:
            self._auth = authorization
        else:
            auth_options = {
                key: value
                for key, value in configuration.items()
                if key not in ["storage", "connection_manager", "handlers"]
            }
            self._auth = Authorization(
                storage=self._options.storage,
                connection_manager=connection_manager,
                handlers=options.authorization_handlers,
                **auth_options,
            )

    @property
    def adapter(self) -> ChannelServiceAdapter:
        """
        The bot's adapter.
        """

        if not self._adapter:
            logger.error(
                "AgentApplication.adapter(): self._adapter is not configured.",
                stack_info=True,
            )
            raise ApplicationError(
                """
                The AgentApplication.adapter property is unavailable because it was 
                not configured when creating the AgentApplication.
                """
            )

        return self._adapter

    @property
    def auth(self):
        """
        The application's authentication manager
        """
        if not self._auth:
            logger.error(
                "AgentApplication.auth(): self._auth is not configured.",
                stack_info=True,
            )
            raise ApplicationError(
                """
                The `AgentApplication.auth` property is unavailable because
                no Auth options were configured.
                """
            )

        return self._auth

    @property
    def options(self) -> ApplicationOptions:
        """
        The application's configured options.
        """
        return self._options

    def activity(
        self,
        activity_type: Union[str, ActivityTypes, List[Union[str, ActivityTypes]]],
        *,
        auth_handlers: Optional[List[str]] = None,
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Registers a new activity event listener. This method can be used as either
        a decorator or a method.

        ```python
        # Use this method as a decorator
        @app.activity("event")
        async def on_event(context: TurnContext, state: TurnState):
            print("hello world!")
            return True
        ```

        #### Args:
        - `type`: The type of the activity
        """

        def __selector(context: TurnContext):
            return activity_type == context.activity.type

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug(
                f"Registering activity handler for route handler {func.__name__} with type: {activity_type} with auth handlers: {auth_handlers}"
            )
            self._routes.append(
                Route[StateT](__selector, func, auth_handlers=auth_handlers)
            )
            return func

        return __call

    def message(
        self,
        select: Union[str, Pattern[str], List[Union[str, Pattern[str]]]],
        *,
        auth_handlers: Optional[List[str]] = None,
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Registers a new message activity event listener. This method can be used as either
        a decorator or a method.

        ```python
        # Use this method as a decorator
        @app.message("hi")
        async def on_hi_message(context: TurnContext, state: TurnState):
            print("hello!")
            return True

        #### Args:
        - `select`: a string or regex pattern
        """

        def __selector(context: TurnContext):
            if context.activity.type != ActivityTypes.message:
                return False

            text = context.activity.text if context.activity.text else ""
            if isinstance(select, Pattern):
                hits = re.fullmatch(select, text)
                return hits is not None

            return text == select

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug(
                f"Registering message handler for route handler {func.__name__} with select: {select} with auth handlers: {auth_handlers}"
            )
            self._routes.append(
                Route[StateT](__selector, func, auth_handlers=auth_handlers)
            )
            return func

        return __call

    def conversation_update(
        self,
        type: ConversationUpdateTypes,
        *,
        auth_handlers: Optional[List[str]] = None,
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Registers a new message activity event listener. This method can be used as either
        a decorator or a method.

        ```python
        # Use this method as a decorator
        @app.conversation_update("channelCreated")
        async def on_channel_created(context: TurnContext, state: TurnState):
            print("a new channel was created!")
            return True

        ```

        #### Args:
        - `type`: a string or regex pattern
        """

        def __selector(context: TurnContext):
            if context.activity.type != ActivityTypes.conversation_update:
                return False

            if type == "membersAdded":
                if isinstance(context.activity.members_added, List):
                    return len(context.activity.members_added) > 0
                return False

            if type == "membersRemoved":
                if isinstance(context.activity.members_removed, List):
                    return len(context.activity.members_removed) > 0
                return False

            if isinstance(context.activity.channel_data, object):
                data = vars(context.activity.channel_data)
                return data["event_type"] == type

            return False

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug(
                f"Registering conversation update handler for route handler {func.__name__} with type: {type} with auth handlers: {auth_handlers}"
            )
            self._routes.append(
                Route[StateT](__selector, func, auth_handlers=auth_handlers)
            )
            return func

        return __call

    def message_reaction(
        self, type: MessageReactionTypes, *, auth_handlers: Optional[List[str]] = None
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Registers a new message activity event listener. This method can be used as either
        a decorator or a method.

        ```python
        # Use this method as a decorator
        @app.message_reaction("reactionsAdded")
        async def on_reactions_added(context: TurnContext, state: TurnState):
            print("reactions was added!")
            return True
        ```

        #### Args:
        - `type`: a string or regex pattern
        """

        def __selector(context: TurnContext):
            if context.activity.type != ActivityTypes.message_reaction:
                return False

            if type == "reactionsAdded":
                if isinstance(context.activity.reactions_added, List):
                    return len(context.activity.reactions_added) > 0
                return False

            if type == "reactionsRemoved":
                if isinstance(context.activity.reactions_removed, List):
                    return len(context.activity.reactions_removed) > 0
                return False

            return False

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug(
                f"Registering message reaction handler for route handler {func.__name__} with type: {type} with auth handlers: {auth_handlers}"
            )
            self._routes.append(
                Route[StateT](__selector, func, auth_handlers=auth_handlers)
            )
            return func

        return __call

    def message_update(
        self, type: MessageUpdateTypes, *, auth_handlers: Optional[List[str]] = None
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Registers a new message activity event listener. This method can be used as either
        a decorator or a method.

        ```python
        # Use this method as a decorator
        @app.message_update("editMessage")
        async def on_edit_message(context: TurnContext, state: TurnState):
            print("message was edited!")
            return True
        ```

        #### Args:
        - `type`: a string or regex pattern
        """

        def __selector(context: TurnContext):
            if type == "editMessage":
                if (
                    context.activity.type == ActivityTypes.message_update
                    and isinstance(context.activity.channel_data, dict)
                ):
                    data = context.activity.channel_data
                    return data["event_type"] == type
                return False

            if type == "softDeleteMessage":
                if (
                    context.activity.type == ActivityTypes.message_delete
                    and isinstance(context.activity.channel_data, dict)
                ):
                    data = context.activity.channel_data
                    return data["event_type"] == type
                return False

            if type == "undeleteMessage":
                if (
                    context.activity.type == ActivityTypes.message_update
                    and isinstance(context.activity.channel_data, dict)
                ):
                    data = context.activity.channel_data
                    return data["event_type"] == type
                return False
            return False

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug(
                f"Registering message update handler for route handler {func.__name__} with type: {type} with auth handlers: {auth_handlers}"
            )
            self._routes.append(
                Route[StateT](__selector, func, auth_handlers=auth_handlers)
            )
            return func

        return __call

    def handoff(self, *, auth_handlers: Optional[List[str]] = None) -> Callable[
        [Callable[[TurnContext, StateT, str], Awaitable[None]]],
        Callable[[TurnContext, StateT, str], Awaitable[None]],
    ]:
        """
        Registers a handler to handoff conversations from one copilot to another.
         ```python
        # Use this method as a decorator
        @app.handoff
        async def on_handoff(
            context: TurnContext, state: TurnState, continuation: str
        ):
            print(query)
        ```
        """

        def __selector(context: TurnContext) -> bool:
            return (
                context.activity.type == ActivityTypes.invoke
                and context.activity.name == "handoff/action"
            )

        def __call(
            func: Callable[[TurnContext, StateT, str], Awaitable[None]],
        ) -> Callable[[TurnContext, StateT, str], Awaitable[None]]:
            async def __handler(context: TurnContext, state: StateT):
                if not context.activity.value:
                    return False
                await func(context, state, context.activity.value["continuation"])
                await context.send_activity(
                    Activity(
                        type=ActivityTypes.invoke_response,
                        value=InvokeResponse(status=200),
                    )
                )
                return True

            logger.debug(
                f"Registering handoff handler for route handler {func.__name__} with auth handlers: {auth_handlers}"
            )

            self._routes.append(
                Route[StateT](__selector, __handler, True, auth_handlers)
            )
            self._routes = sorted(self._routes, key=lambda route: not route.is_invoke)
            return func

        return __call

    def on_sign_in_success(
        self, func: Callable[[TurnContext, StateT, Optional[str]], Awaitable[None]]
    ) -> Callable[[TurnContext, StateT, Optional[str]], Awaitable[None]]:
        """
        Registers a new event listener that will be executed when a user successfully signs in.

        ```python
        # Use this method as a decorator
        @app.on_sign_in_success
        async def sign_in_success(context: TurnContext, state: TurnState):
            print("hello world!")
            return True
        ```
        """

        if self._auth:
            logger.debug(
                f"Registering sign-in success handler for route handler {func.__name__}"
            )
            self._auth.on_sign_in_success(func)
        else:
            logger.error(
                f"Failed to register sign-in success handler for route handler {func.__name__}",
                stack_info=True,
            )
            raise ApplicationError(
                """
                The `AgentApplication.on_sign_in_success` method is unavailable because
                no Auth options were configured.
                """
            )
        return func

    def on_sign_in_failure(
        self, func: Callable[[TurnContext, StateT, Optional[str]], Awaitable[None]]
    ) -> Callable[[TurnContext, StateT, Optional[str]], Awaitable[None]]:
        """
        Registers a new event listener that will be executed when a user fails to sign in.

        ```python
        # Use this method as a decorator
        @app.on_sign_in_failure
        async def sign_in_failure(context: TurnContext, state: TurnState):
            print("hello world!")
            return True
        ```
        """

        if self._auth:
            logger.debug(
                f"Registering sign-in failure handler for route handler {func.__name__}"
            )
            self._auth.on_sign_in_failure(func)
        else:
            logger.error(
                f"Failed to register sign-in failure handler for route handler {func.__name__}",
                stack_info=True,
            )
            raise ApplicationError(
                """
                The `AgentApplication.on_sign_in_failure` method is unavailable because
                no Auth options were configured.
                """
            )
        return func

    def error(
        self, func: Callable[[TurnContext, Exception], Awaitable[None]]
    ) -> Callable[[TurnContext, Exception], Awaitable[None]]:
        """
        Registers an error handler that will be called anytime
        the app throws an Exception

        ```python
        # Use this method as a decorator
        @app.error
        async def on_error(context: TurnContext, err: Exception):
            print(err.message)
        ```
        """

        logger.debug(f"Registering the error handler {func.__name__} ")
        self._error = func

        if self._adapter:
            logger.debug(
                f"Registering for adapter {self._adapter.__class__.__name__} the error handler {func.__name__} "
            )
            self._adapter.on_turn_error = func

        return func

    def turn_state_factory(self, func: Callable[[TurnContext], Awaitable[StateT]]):
        """
        Custom Turn State Factory
        """
        logger.debug(f"Setting custom turn state factory: {func.__name__}")
        self._turn_state_factory = func
        return func

    async def on_turn(self, context: TurnContext):
        logger.debug(
            f"AgentApplication.on_turn(): Processing turn for context: {context.activity.id}"
        )
        await self._start_long_running_call(context, self._on_turn)

    async def _on_turn(self, context: TurnContext):
        try:
            await self._start_typing(context)

            self._remove_mentions(context)

            logger.debug("Initializing turn state")
            turn_state = await self._initialize_state(context)

            sign_in_state = turn_state.get_value(
                Authorization.SIGN_IN_STATE_KEY, target_cls=SignInState
            )
            logger.debug(
                f"Sign-in state: {sign_in_state} for context: {context.activity.id}"
            )

            if self._auth and sign_in_state and not sign_in_state.completed:
                flow_state = self._auth.get_flow_state(sign_in_state.handler_id)
                logger.debug("Flow state: %s", flow_state)
                if flow_state.flow_started:
                    logger.debug("Continuing sign-in flow")
                    token_response = await self._auth.begin_or_continue_flow(
                        context, turn_state, sign_in_state.handler_id
                    )
                    saved_activity = sign_in_state.continuation_activity.model_copy()
                    if token_response and token_response.token:
                        new_context = copy(context)
                        new_context.activity = saved_activity
                        logger.info(
                            "Resending continuation activity %s", saved_activity.text
                        )
                        await self.on_turn(new_context)
                        turn_state.delete_value(Authorization.SIGN_IN_STATE_KEY)
                        await turn_state.save(context)
                    return

            logger.debug("Running before turn middleware")
            if not await self._run_before_turn_middleware(context, turn_state):
                return

            logger.debug("Running file downloads")
            await self._handle_file_downloads(context, turn_state)

            logger.debug("Running activity handlers")
            await self._on_activity(context, turn_state)

            logger.debug("Running after turn middleware")
            if not await self._run_after_turn_middleware(context, turn_state):
                await turn_state.save(context)
            return
        except ApplicationError as err:
            logger.error(
                f"An application error occurred in the AgentApplication: {err}",
                exc_info=True,
            )
            await self._on_error(context, err)
        finally:
            logger.debug("Stopping typing indicator")
            self.typing.stop()

    async def _start_typing(self, context: TurnContext):
        if self._options.start_typing_timer:
            logger.debug("Starting typing indicator for context")
            await self.typing.start(context)

    def _remove_mentions(self, context: TurnContext):
        if (
            self.options.remove_recipient_mention
            and context.activity.type == ActivityTypes.message
        ):
            context.activity.text = context.remove_recipient_mention(context.activity)

    @staticmethod
    def parse_env_vars_configuration(vars: Dict[str, Any]) -> dict:
        """
        Parses environment variables and returns a dictionary with the relevant configuration.
        """
        result = {}
        for key, value in vars.items():
            levels = key.split("__")
            current_level = result
            last_level = None
            for next_level in levels:
                if next_level not in current_level:
                    current_level[next_level] = {}
                last_level = current_level
                current_level = current_level[next_level]
            logger.debug(f"Using environment variable '{key}'")
            last_level[levels[-1]] = value

        return {
            "AGENT_APPLICATION": result["AGENT_APPLICATION"],
            "COPILOT_STUDIO_AGENT": result["COPILOT_STUDIO_AGENT"],
            "CONNECTIONS": result["CONNECTIONS"],
            "CONNECTIONS_MAP": result["CONNECTIONS_MAP"],
        }

    async def _initialize_state(self, context: TurnContext) -> StateT:
        if self._turn_state_factory:
            logger.debug("Using custom turn state factory")
            turn_state = self._turn_state_factory()
        else:
            logger.debug("Using default turn state factory")
            turn_state = TurnState.with_storage(self._options.storage)
            await turn_state.load(context, self._options.storage)

        turn_state = cast(StateT, turn_state)

        logger.debug("Loading turn state from storage")
        await turn_state.load(context, self._options.storage)
        turn_state.temp.input = context.activity.text
        return turn_state

    async def _run_before_turn_middleware(self, context: TurnContext, state: StateT):
        for before_turn in self._internal_before_turn:
            is_ok = await before_turn(context, state)
            if not is_ok:
                await state.save(context, self._options.storage)
                return False
        return True

    async def _handle_file_downloads(self, context: TurnContext, state: StateT):
        if self._options.file_downloaders and len(self._options.file_downloaders) > 0:
            input_files = state.temp.input_files if state.temp.input_files else []
            for file_downloader in self._options.file_downloaders:
                logger.info(
                    f"Using file downloader: {file_downloader.__class__.__name__}"
                )
                files = await file_downloader.download_files(context)
                input_files.extend(files)
            state.temp.input_files = input_files

    def _contains_non_text_attachments(self, context: TurnContext):
        non_text_attachments = filter(
            lambda a: not a.content_type.startswith("text/html"),
            context.activity.attachments,
        )
        return len(list(non_text_attachments)) > 0

    async def _run_after_turn_middleware(self, context: TurnContext, state: StateT):
        for after_turn in self._internal_after_turn:
            is_ok = await after_turn(context, state)
            if not is_ok:
                await state.save(context, self._options.storage)
                return False
        return True

    async def _on_activity(self, context: TurnContext, state: StateT):
        for route in self._routes:
            if route.selector(context):
                if not route.auth_handlers:
                    await route.handler(context, state)
                else:
                    sign_in_complete = False
                    for auth_handler_id in route.auth_handlers:
                        token_response = await self._auth.begin_or_continue_flow(
                            context, state, auth_handler_id
                        )
                        sign_in_complete = token_response and token_response.token
                        if not sign_in_complete:
                            break
                    if sign_in_complete:
                        await route.handler(context, state)
                return
        logger.warning(
            f"No route found for activity type: {context.activity.type} with text: {context.activity.text}"
        )

    async def _start_long_running_call(
        self, context: TurnContext, func: Callable[[TurnContext], Awaitable]
    ):
        if (
            self._adapter
            and ActivityTypes.message == context.activity.type
            and self._options.long_running_messages
        ):
            logger.debug(
                f"Starting long running call for context: {context.activity.id} with function: {func.__name__}"
            )
            return await self._adapter.continue_conversation(
                reference=context.get_conversation_reference(context.activity),
                callback=func,
                bot_app_id=self.options.bot_app_id,
            )

        return await func(context)

    async def _on_error(self, context: TurnContext, err: ApplicationError) -> None:
        if self._error:
            logger.info(
                f"Calling error handler {self._error.__name__} for error: {err}"
            )
            return await self._error(context, err)

        logger.error(
            f"An error occurred in the AgentApplication: {err}",
            exc_info=True,
        )
        logger.error(err)
        raise err
