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
    Generic,
    Optional,
    Pattern,
    TypeVar,
    Union,
    cast,
)

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ConversationUpdateTypes,
    MessageReactionTypes,
    MessageUpdateTypes,
    InvokeResponse,
)

from ..turn_context import TurnContext
from ..agent import Agent
from ..authorization import Connections
from .app_error import ApplicationError
from .app_options import ApplicationOptions

from .state import TurnState
from ..channel_service_adapter import ChannelServiceAdapter
from .oauth import Authorization
from .typing_indicator import TypingIndicator

from ._type_defs import RouteHandler, RouteSelector
from ._routes import _RouteList, _Route, RouteRank, _agentic_selector

logger = logging.getLogger(__name__)

StateT = TypeVar("StateT", bound=TurnState)


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
    _internal_before_turn: list[Callable[[TurnContext, StateT], Awaitable[bool]]] = []
    _internal_after_turn: list[Callable[[TurnContext, StateT], Awaitable[bool]]] = []
    _route_list: _RouteList[StateT] = _RouteList[StateT]()
    _error: Optional[Callable[[TurnContext, Exception], Awaitable[None]]] = None
    _turn_state_factory: Optional[Callable[[TurnContext], StateT]] = None

    def __init__(
        self,
        options: Optional[ApplicationOptions] = None,
        *,
        connection_manager: Optional[Connections] = None,
        authorization: Optional[Authorization] = None,
        **kwargs,
    ) -> None:
        """
        Creates a new AgentApplication instance.

        :param options: Configuration options for the application.
        :type options: Optional[:class:`microsoft_agents.hosting.core.app.app_options.ApplicationOptions`]
        :param connection_manager: OAuth connection manager.
        :type connection_manager: Optional[:class:`microsoft_agents.hosting.core.authorization.Connections`]
        :param authorization: Authorization manager for handling authentication flows.
        :type authorization: Optional[:class:`microsoft_agents.hosting.core.app.oauth.Authorization`]
        :param kwargs: Additional configuration parameters.
        :type kwargs: Any
        """
        self._route_list = _RouteList[StateT]()

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

        :return: The channel service adapter for the bot.
        :rtype: :class:`microsoft_agents.hosting.core.channel_service_adapter.ChannelServiceAdapter`
        :raises ApplicationError: If the adapter is not configured.
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
    def auth(self) -> Authorization:
        """
        The application's authentication manager

        :return: The authentication manager for handling OAuth flows.
        :rtype: :class:`microsoft_agents.hosting.core.app.oauth.Authorization`
        :raises ApplicationError: If authentication is not configured.
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

        :return: The configuration options for the application.
        :rtype: :class:`microsoft_agents.hosting.core.app.app_options.ApplicationOptions`
        """
        return self._options

    def add_route(
        self,
        selector: RouteSelector,
        handler: RouteHandler[StateT],
        is_invoke: bool = False,
        is_agentic: bool = False,
        rank: RouteRank = RouteRank.DEFAULT,
        auth_handlers: Optional[list[str]] = None,
    ) -> None:
        """Adds a new route to the application.

        Routes are ordered by: is_agentic, is_invoke, rank (lower is higher priority), in that order.

        :param selector: A function that takes a TurnContext and returns a boolean indicating whether the route should be selected.
        :type selector: Callable[[:class:`microsoft_agents.hosting.core.turn_context.TurnContext`], bool]
        :param handler: A function that takes a TurnContext and a TurnState and returns an Awaitable.
        :type handler: :class:`microsoft_agents.hosting.core.app._type_defs.RouteHandler`[StateT]
        :param is_invoke: Whether the route is for an invoke activity, defaults to False
        :type is_invoke: bool, Optional
        :param is_agentic: Whether the route is for an agentic request, defaults to False. For agentic requests
            the selector will include a new check for `context.activity.is_agentic_request()`.
        :type is_agentic: bool, Optional
        :param rank: The rank of the route, defaults to RouteRank.DEFAULT
        :type rank: :class:`microsoft_agents.hosting.core.app._routes.route_rank.RouteRank`, Optional
        :param auth_handlers: A list of authentication handler IDs to use for this route, defaults to None
        :type auth_handlers: Optional[list[str]], Optional
        :raises ApplicationError: If the selector or handler are not valid.
        """
        if not selector or not handler:
            logger.error(
                "AgentApplication.add_route(): selector and handler are required."
            )
            raise ApplicationError("selector and handler are required.")

        if is_agentic:
            selector = _agentic_selector(selector)

        route = _Route[StateT](
            selector, handler, is_invoke, rank, auth_handlers, is_agentic
        )
        self._route_list.add_route(route)

    def activity(
        self,
        activity_type: Union[str, ActivityTypes, list[Union[str, ActivityTypes]]],
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Register a new activity event listener as either a decorator or a method.

        Example:
            .. code-block:: python

                @app.activity("event")
                async def on_event(context: TurnContext, state: TurnState):
                    print("hello world!")
                    return True

        :param activity_type: Activity type or collection of types that should trigger the handler.
        :type activity_type: Union[str, microsoft_agents.activity.ActivityTypes, list[Union[str, microsoft_agents.activity.ActivityTypes]]]
        :param auth_handlers: Optional list of authorization handler IDs for the route.
        :type auth_handlers: Optional[list[str]]
        :param kwargs: Additional route configuration passed to :meth:`add_route`.
        """

        def __selector(context: TurnContext):
            return activity_type == context.activity.type

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug(
                f"Registering activity handler for route handler {func.__name__} with type: {activity_type} with auth handlers: {auth_handlers}"
            )
            self.add_route(__selector, func, auth_handlers=auth_handlers, **kwargs)
            return func

        return __call

    def message(
        self,
        select: Union[str, Pattern[str], list[Union[str, Pattern[str]]]],
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Register a new message activity event listener as either a decorator or a method.

        Example:
            .. code-block:: python

                @app.message("hi")
                async def on_hi_message(context: TurnContext, state: TurnState):
                    print("hello!")
                    return True

        :param select: Literal text, compiled regex, or list of either used to match the incoming message.
        :type select: Union[str, Pattern[str], list[Union[str, Pattern[str]]]]
        :param auth_handlers: Optional list of authorization handler IDs for the route.
        :type auth_handlers: Optional[list[str]]
        :param kwargs: Additional route configuration passed to :meth:`add_route`.
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
            self.add_route(__selector, func, auth_handlers=auth_handlers, **kwargs)
            return func

        return __call

    def conversation_update(
        self,
        type: ConversationUpdateTypes,
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Register a handler for conversation update activities as either a decorator or a method.

        Example:
            .. code-block:: python

                @app.conversation_update("channelCreated")
                async def on_channel_created(context: TurnContext, state: TurnState):
                    print("a new channel was created!")
                    return True

        :param type: Conversation update category that must match the incoming activity.
        :type type: microsoft_agents.activity.ConversationUpdateTypes
        :param auth_handlers: Optional list of authorization handler IDs for the route.
        :type auth_handlers: Optional[list[str]]
        :param kwargs: Additional route configuration passed to :meth:`add_route`.
        """

        def __selector(context: TurnContext):
            if context.activity.type != ActivityTypes.conversation_update:
                return False

            if type == "membersAdded":
                if isinstance(context.activity.members_added, list):
                    return len(context.activity.members_added) > 0
                return False

            if type == "membersRemoved":
                if isinstance(context.activity.members_removed, list):
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
            self.add_route(__selector, func, auth_handlers=auth_handlers, **kwargs)
            return func

        return __call

    def message_reaction(
        self,
        type: MessageReactionTypes,
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Register a handler for message reaction activities as either a decorator or a method.

        Example:
            .. code-block:: python

                @app.message_reaction("reactionsAdded")
                async def on_reactions_added(context: TurnContext, state: TurnState):
                    print("reaction was added!")
                    return True

        :param type: Reaction category that must match the incoming activity.
        :type type: microsoft_agents.activity.MessageReactionTypes
        :param auth_handlers: Optional list of authorization handler IDs for the route.
        :type auth_handlers: Optional[list[str]]
        :param kwargs: Additional route configuration passed to :meth:`add_route`.
        """

        def __selector(context: TurnContext):
            if context.activity.type != ActivityTypes.message_reaction:
                return False

            if type == "reactionsAdded":
                if isinstance(context.activity.reactions_added, list):
                    return len(context.activity.reactions_added) > 0
                return False

            if type == "reactionsRemoved":
                if isinstance(context.activity.reactions_removed, list):
                    return len(context.activity.reactions_removed) > 0
                return False

            return False

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            logger.debug(
                f"Registering message reaction handler for route handler {func.__name__} with type: {type} with auth handlers: {auth_handlers}"
            )
            self.add_route(__selector, func, auth_handlers=auth_handlers, **kwargs)
            return func

        return __call

    def message_update(
        self,
        type: MessageUpdateTypes,
        *,
        auth_handlers: Optional[list[str]] = None,
        **kwargs,
    ) -> Callable[[RouteHandler[StateT]], RouteHandler[StateT]]:
        """
        Register a handler for message update activities as either a decorator or a method.

        Example:
            .. code-block:: python

                @app.message_update("editMessage")
                async def on_edit_message(context: TurnContext, state: TurnState):
                    print("message was edited!")
                    return True

        :param type: Message update category that must match the incoming activity.
        :type type: microsoft_agents.activity.MessageUpdateTypes
        :param auth_handlers: Optional list of authorization handler IDs for the route.
        :type auth_handlers: Optional[list[str]]
        :param kwargs: Additional route configuration passed to :meth:`add_route`.
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
            self.add_route(__selector, func, auth_handlers=auth_handlers, **kwargs)
            return func

        return __call

    def handoff(
        self, *, auth_handlers: Optional[list[str]] = None, **kwargs
    ) -> Callable[
        [Callable[[TurnContext, StateT, str], Awaitable[None]]],
        Callable[[TurnContext, StateT, str], Awaitable[None]],
    ]:
        """
        Register a handler to hand off conversations from one copilot to another.

        Example:
            .. code-block:: python

                @app.handoff
                async def on_handoff(context: TurnContext, state: TurnState, continuation: str):
                    print(continuation)

        :param auth_handlers: Optional list of authorization handler IDs for the route.
        :type auth_handlers: Optional[list[str]]
        :param kwargs: Additional route configuration passed to :meth:`add_route`.
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

            self.add_route(__selector, func, auth_handlers=auth_handlers, **kwargs)
            return func

        return __call

    def on_sign_in_success(
        self, func: Callable[[TurnContext, StateT, Optional[str]], Awaitable[None]]
    ) -> Callable[[TurnContext, StateT, Optional[str]], Awaitable[None]]:
        """
        Register a callback that executes when a user successfully signs in.

        Example:
            .. code-block:: python

                @app.on_sign_in_success
                async def sign_in_success(context: TurnContext, state: TurnState, connection_id: str | None):
                    print("sign-in succeeded")

        :param func: Callable that handles the sign-in success event.
        :type func: Callable[[TurnContext, StateT, Optional[str]], Awaitable[None]]
        :raises ApplicationError: If authorization services are not configured.
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
        Register a callback that executes when a user fails to sign in.

        Example:
            .. code-block:: python

                @app.on_sign_in_failure
                async def sign_in_failure(context: TurnContext, state: TurnState, connection_id: str | None):
                    print("sign-in failed")

        :param func: Callable that handles the sign-in failure event.
        :type func: Callable[[TurnContext, StateT, Optional[str]], Awaitable[None]]
        :raises ApplicationError: If authorization services are not configured.
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
        Register an error handler that is invoked whenever the application raises an exception.

        Example:
            .. code-block:: python

                @app.error
                async def on_error(context: TurnContext, err: Exception):
                    print(err)

        :param func: Callable executed when an uncaught exception occurs during a turn.
        :type func: Callable[[TurnContext, Exception], Awaitable[None]]
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
        typing = None
        try:
            if context.activity.type != ActivityTypes.typing:
                if self._options.start_typing_timer:
                    typing = TypingIndicator()
                    await typing.start(context)

            self._remove_mentions(context)

            logger.debug("Initializing turn state")
            turn_state = await self._initialize_state(context)
            if (
                context.activity.type == ActivityTypes.message
                or context.activity.type == ActivityTypes.invoke
            ):

                (
                    auth_intercepts,
                    continuation_activity,
                ) = await self._auth._on_turn_auth_intercept(context, turn_state)
                if auth_intercepts:
                    if continuation_activity:
                        new_context = copy(context)
                        new_context.activity = continuation_activity
                        logger.info(
                            "Resending continuation activity %s",
                            continuation_activity.text,
                        )
                        await self.on_turn(new_context)
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
            if await self._run_after_turn_middleware(context, turn_state):
                await turn_state.save(context)
            return
        except ApplicationError as err:
            logger.error(
                f"An application error occurred in the AgentApplication: {err}",
                exc_info=True,
            )
            await self._on_error(context, err)
        finally:
            if typing:
                await typing.stop()

    def _remove_mentions(self, context: TurnContext):
        if (
            self.options.remove_recipient_mention
            and context.activity.type == ActivityTypes.message
        ):
            context.activity.text = context.remove_recipient_mention(context.activity)

    @staticmethod
    def parse_env_vars_configuration(vars: dict[str, Any]) -> dict:
        """
        Parses environment variables and returns a dictionary with the relevant configuration.

        :param vars: Dictionary of environment variable names and values.
        :type vars: dict[str, Any]
        :return: Parsed configuration dictionary with nested structure.
        :rtype: dict
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
                await state.save(context)
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
                await state.save(context)
                return False
        return True

    async def _on_activity(self, context: TurnContext, state: StateT):
        for route in self._route_list:
            if route.selector(context):
                if not route.auth_handlers:
                    await route.handler(context, state)
                else:
                    sign_in_complete = True
                    for auth_handler_id in route.auth_handlers:
                        if not (
                            await self._auth._start_or_continue_sign_in(
                                context, state, auth_handler_id
                            )
                        ).sign_in_complete():
                            sign_in_complete = False
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
