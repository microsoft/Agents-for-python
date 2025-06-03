"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import re
from typing import (
    Awaitable,
    Callable,
    Generic,
    List,
    Optional,
    Pattern,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from .. import Agent, TurnContext
from microsoft.agents.core.models import (
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
from .typing import Typing

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

    typing: Typing

    _options: ApplicationOptions
    _adapter: Optional[ChannelServiceAdapter] = None
    # _auth: Optional[AuthManager[StateT]] = None
    _before_turn: List[RouteHandler[StateT]] = []
    _after_turn: List[RouteHandler[StateT]] = []
    _routes: List[Route[StateT]] = []
    _error: Optional[Callable[[TurnContext, Exception], Awaitable[None]]] = None
    _turn_state_factory: Optional[Callable[[TurnContext], Awaitable[StateT]]] = None

    def __init__(self, options: ApplicationOptions = None, **kwargs) -> None:
        """
        Creates a new AgentApplication instance.
        """
        self.typing = Typing()
        self._routes = []

        if not options:
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
            raise ApplicationError(
                """
                The `ApplicationOptions.storage` property is required and was not configured.
                """
            )

        if options.long_running_messages and (
            not options.adapter or not options.bot_app_id
        ):
            raise ApplicationError(
                """
                The `ApplicationOptions.long_running_messages` property is unavailable because 
                no adapter or `bot_app_id` was configured.
                """
            )

        if options.adapter:
            self._adapter = options.adapter

        """
        if options.auth:
            self._auth = AuthManager[StateT](default=options.auth.default)

            for name, opts in options.auth.settings.items():
                if isinstance(opts, OAuthOptions):
                    self._auth.set(name, OAuth[StateT](opts))
        """

        # TODO: Disabling AI chain for now
        self._ai = None

    @property
    def adapter(self) -> ChannelServiceAdapter:
        """
        The bot's adapter.
        """

        if not self._adapter:
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
        self, type: Union[str, Pattern[str], List[Union[str, Pattern[str]]]]
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
            return type == context.activity.type

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            self._routes.append(Route[StateT](__selector, func))
            return func

        return __call

    def message(
        self, select: Union[str, Pattern[str], List[Union[str, Pattern[str]]]]
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
                hits = re.match(select, text)
                return hits is not None and len(hits.regs) == 1

            return text == select

        def __call(func: RouteHandler[StateT]) -> RouteHandler[StateT]:
            self._routes.append(Route[StateT](__selector, func))
            return func

        return __call

    def conversation_update(
        self, type: ConversationUpdateTypes
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
            self._routes.append(Route[StateT](__selector, func))
            return func

        return __call

    def message_reaction(
        self, type: MessageReactionTypes
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
            self._routes.append(Route[StateT](__selector, func))
            return func

        return __call

    def message_update(
        self, type: MessageUpdateTypes
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
            self._routes.append(Route[StateT](__selector, func))
            return func

        return __call

    def handoff(
        self,
    ) -> Callable[
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
            async def __handler__(context: TurnContext, state: StateT):
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

            self._routes.append(Route[StateT](__selector, __handler__, True))
            return func

        return __call

    def before_turn(self, func: RouteHandler[StateT]) -> RouteHandler[StateT]:
        """
        Registers a new event listener that will be executed before turns.
        This method can be used as either a decorator or a method and
        is called in the order they are registered.

        ```python
        # Use this method as a decorator
        @app.before_turn
        async def on_before_turn(context: TurnContext, state: TurnState):
            print("hello world!")
            return True
        ```
        """

        self._before_turn.append(func)
        return func

    def after_turn(self, func: RouteHandler[StateT]) -> RouteHandler[StateT]:
        """
        Registers a new event listener that will be executed after turns.
        This method can be used as either a decorator or a method and
        is called in the order they are registered.

        ```python
        # Use this method as a decorator
        @app.after_turn
        async def on_after_turn(context: TurnContext, state: TurnState):
            print("hello world!")
            return True
        ```
        """

        self._after_turn.append(func)
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

        self._error = func

        if self._adapter:
            self._adapter.on_turn_error = func

        return func

    def turn_state_factory(self, func: Callable[[TurnContext], Awaitable[StateT]]):
        """
        Custom Turn State Factory
        """

        self._turn_state_factory = func
        return func

    async def on_turn(self, context: TurnContext):
        await self._start_long_running_call(context, self._on_turn)

    async def _on_turn(self, context: TurnContext):
        try:
            await self._start_typing(context)

            self._remove_mentions(context)

            turn_state = await self._initialize_state(context)

            """
            if not await self._authenticate_user(context, state):
                return
            """

            if not await self._run_before_turn_middleware(context, turn_state):
                return

            await self._handle_file_downloads(context, turn_state)

            await self._on_activity(context, turn_state)

            if not await self._run_after_turn_middleware(context, turn_state):
                await turn_state.save(context)
                return

            await turn_state.save(context)
        except ApplicationError as err:
            await self._on_error(context, err)
        finally:
            self.typing.stop()

    async def _start_typing(self, context: TurnContext):
        if self._options.start_typing_timer:
            await self.typing.start(context)

    def _remove_mentions(self, context: TurnContext):
        if (
            self.options.remove_recipient_mention
            and context.activity.type == ActivityTypes.message
        ):
            context.activity.text = context.remove_recipient_mention(context.activity)

    async def _initialize_state(self, context: TurnContext) -> StateT:
        if self._turn_state_factory:
            turn_state = await self._turn_state_factory()
        else:
            turn_state = TurnState.with_storage(self._options.storage)
            await turn_state.load(context, self._options.storage)

        turn_state = cast(StateT, turn_state)

        await turn_state.load(context, self._options.storage)
        turn_state.temp.input = context.activity.text
        return turn_state

    async def _authenticate_user(self, context: TurnContext, state):
        if self.options.auth and self._auth:
            auth_condition = (
                isinstance(self.options.auth.auto, bool) and self.options.auth.auto
            ) or (callable(self.options.auth.auto) and self.options.auth.auto(context))
            user_in_sign_in = IN_SIGN_IN_KEY in state.user
            if auth_condition or user_in_sign_in:
                key: Optional[str] = state.user.get(
                    IN_SIGN_IN_KEY, self.options.auth.default
                )

                if key is not None:
                    state.user[IN_SIGN_IN_KEY] = key
                    res = await self._auth.sign_in(context, state, key=key)
                    if res.status == "complete":
                        del state.user[IN_SIGN_IN_KEY]

                    if res.status == "pending":
                        await state.save(context, self._options.storage)
                        return False

                    if res.status == "error" and res.reason != "invalid-activity":
                        del state.user[IN_SIGN_IN_KEY]
                        raise ApplicationError(f"[{res.reason}] => {res.message}")

        return True

    async def _run_before_turn_middleware(self, context: TurnContext, state):
        for before_turn in self._before_turn:
            is_ok = await before_turn(context, state)
            if not is_ok:
                await state.save(context, self._options.storage)
                return False
        return True

    async def _handle_file_downloads(self, context: TurnContext, state):
        if self._options.file_downloaders and len(self._options.file_downloaders) > 0:
            input_files = state.temp.input_files if state.temp.input_files else []
            for file_downloader in self._options.file_downloaders:
                files = await file_downloader.download_files(context)
                input_files.extend(files)
            state.temp.input_files = input_files

    async def _run_ai_chain(self, context: TurnContext, state: StateT):
        if (
            self._ai
            and self._options.ai
            and context.activity.type == ActivityTypes.message
            and (context.activity.text or self._contains_non_text_attachments(context))
        ):
            is_ok = await self._ai.run(context, state)
            if not is_ok:
                await state.save(context, self._options.storage)
                return False
        return True

    def _contains_non_text_attachments(self, context: TurnContext):
        non_text_attachments = filter(
            lambda a: not a.content_type.startswith("text/html"),
            context.activity.attachments,
        )
        return len(list(non_text_attachments)) > 0

    async def _run_after_turn_middleware(self, context: TurnContext, state: StateT):
        for after_turn in self._after_turn:
            is_ok = await after_turn(context, state)
            if not is_ok:
                await state.save(context, self._options.storage)
                return False
        return True

    async def _on_activity(self, context: TurnContext, state: StateT):
        # ensure we handle invokes first
        routes = filter(lambda r: not r.is_invoke and r.selector(context), self._routes)
        invoke_routes = filter(
            lambda r: r.is_invoke and r.selector(context), self._routes
        )

        for route in invoke_routes:
            if route.selector(context):
                await route.handler(context, state)
                return

        for route in routes:
            if route.selector(context):
                await route.handler(context, state)
                return

    async def _start_long_running_call(
        self, context: TurnContext, func: Callable[[TurnContext], Awaitable]
    ):
        if (
            self._adapter
            and ActivityTypes.message == context.activity.type
            and self._options.long_running_messages
        ):
            return await self._adapter.continue_conversation(
                reference=context.get_conversation_reference(context.activity),
                callback=func,
                bot_app_id=self.options.bot_app_id,
            )

        return await func(context)

    async def _on_error(self, context: TurnContext, err: ApplicationError) -> None:
        if self._error:
            return await self._error(context, err)

        self._options.logger.error(err)
        raise err
