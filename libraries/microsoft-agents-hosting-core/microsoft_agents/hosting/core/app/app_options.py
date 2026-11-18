"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Self

from microsoft_agents.activity.config import (
    Configuration,
    _RootConfigurable,
    ignore_case,
    _legpath as legpath,
)

from microsoft_agents.hosting.core.app.oauth import AuthHandlerConfig
from microsoft_agents.hosting.core.storage import Storage

# from .auth import AuthOptions
from .typing_indicator import TypingOptions
from .input_file import InputFileDownloader
from ..channel_service_adapter import ChannelServiceAdapter

from .state.turn_state import TurnState
from .proactive.proactive_options import ProactiveOptions


@dataclass
class ApplicationOptions(_RootConfigurable):
    adapter: ChannelServiceAdapter | None = None
    """
    Optional. Options used to initialize your `BotAdapter`
    """

    bot_app_id: str = ""
    """
    Optional. `AgentApplication` ID of the bot.
    """

    storage: Storage | None = None
    """
    Optional. `Storage` provider to use for the application.
    """

    remove_recipient_mention: bool = True
    """
    Optional. If true, the bot will automatically remove mentions of the bot's name from incoming
    messages. Defaults to true.
    """

    start_typing_timer: bool = True
    """
    Optional. If true, the bot will automatically start a typing timer when messages are received.
    This allows the bot to automatically indicate that it's received the message and is processing
    the request. Defaults to true.
    """

    typing: TypingOptions | None = None
    """
    Optional. Typing indicator timing options. Controls initial delay, interval,
    and per-channel strategies. If not provided, defaults are used when
    ``start_typing_timer`` is true.
    """

    long_running_messages: bool = False
    """
    Optional. If true, the bot supports long running messages that can take longer then the 10 - 15
    second timeout imposed by most channels. Defaults to false.

    This works by immediately converting the incoming request to a proactive conversation.
    Care should be used for bots that operate in a shared hosting environment. 
    The incoming request is immediately completed and many shared hosting environments 
    will mark the bot's process as idle and shut it down.
    """

    file_downloaders: list[InputFileDownloader] = field(default_factory=list)
    """
    Optional. Array of input file download plugins to use. 
    """

    turn_state_factory: Callable[[], TurnState] | None = None
    """
    Optional. Factory function to create the turn state.
    This should return an instance of `TurnState` or a subclass.
    If not provided, the default `TurnState` will be used.
    """

    authorization_handlers: dict[str, AuthHandlerConfig] | None = None
    """
    Optional dictionary of sign-in handler IDs and AuthHandlerConfig objects.
    A nonempty dictionary replaces handlers from application configuration when
    AgentApplication creates Authorization. An empty dictionary or None uses
    configured handlers instead; it does not disable them.
    Use AuthHandlerConfig rather than the deprecated AuthHandler constructor.
    """

    proactive: ProactiveOptions | None = None
    """
    Optional. Options for the proactive messaging subsystem.
    When set, :attr:`microsoft_agents.hosting.core.AgentApplication.proactive` is available for storing
    conversations and initiating proactive turns.
    """

    @classmethod
    def _from_scoped_configuration(cls, config: Configuration) -> Self:
        auth_handlers = config.get(legpath("authorization_handlers"), None)
        if auth_handlers is not None and not isinstance(auth_handlers, Mapping):
            raise TypeError("authorization_handlers must be a mapping")

        storage = config.get("storage")
        if storage is not None and not isinstance(storage, Storage):
            raise TypeError("storage must be an instance of Storage or None")

        proactive_options = config.get("proactive")
        if proactive_options is not None and not isinstance(
            proactive_options, ProactiveOptions
        ):
            raise TypeError("proactive must be an instance of ProactiveOptions or None")

        turn_state_factory = config.get("turn_state_factory")

        file_downloaders = config.get("file_downloaders")
        if file_downloaders is not None and isinstance(file_downloaders, list):
            if file_downloaders:
                for downloader in file_downloaders:
                    if not isinstance(downloader, InputFileDownloader):
                        raise TypeError(
                            "each item in file_downloaders must be an instance of FileDownloader"
                        )
        elif file_downloaders is not None and not isinstance(file_downloaders, list):
            raise TypeError("file_downloaders must be a list or None")
        file_downloaders = file_downloaders or []

        adapter = config.get("adapter")
        if adapter is not None and not isinstance(adapter, ChannelServiceAdapter):
            raise TypeError("adapter must be an instance of Adapter or None")

        return ApplicationOptions(
            bot_app_id=config.get_str(legpath("bot_app_id"), ""),
            start_typing_timer=config.get(legpath("start_typing_timer"), True),
            remove_recipient_mention=config.get(
                legpath("remove_recipient_mention"), True
            ),
            long_running_messages=config.get(legpath("long_running_messages"), False),
            authorization_handlers=auth_handlers,
            storage=storage,
            proactive=proactive_options,
            turn_state_factory=turn_state_factory,
            file_downloaders=file_downloaders,
            adapter=adapter,
        )

    @classmethod
    def _from_root_configuration(cls, config: Configuration) -> Self:
        return cls._from_scoped_configuration(
            config.get_section(ignore_case("AgentApplication"), default=Configuration())
        )
