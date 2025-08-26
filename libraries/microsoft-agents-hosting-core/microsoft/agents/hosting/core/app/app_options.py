"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from logging import Logger
from typing import Callable, List, Optional

from microsoft.agents.hosting.core.app.oauth.authorization import AuthorizationHandlers
from microsoft.agents.hosting.core.storage import Storage

# from .auth import AuthOptions
from .input_file import InputFileDownloader
from ..channel_service_adapter import ChannelServiceAdapter

from .state.turn_state import TurnState

# from .teams_adapter import TeamsAdapter


@dataclass
class ApplicationOptions:
    adapter: Optional[ChannelServiceAdapter] = None
    """
    Optional. Options used to initialize your `BotAdapter`
    """

    # auth: Optional[AuthOptions] = None
    """
    Optional. Auth settings.
    """

    bot_app_id: str = ""
    """
    Optional. `AgentApplication` ID of the bot.
    """

    storage: Optional[Storage] = None
    """
    Optional. `Storage` provider to use for the application.
    """

    logger: Logger = Logger(__name__)
    """
    Optional. `Logger` that will be used in this application.
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

    long_running_messages: bool = False
    """
    Optional. If true, the bot supports long running messages that can take longer then the 10 - 15
    second timeout imposed by most channels. Defaults to false.

    This works by immediately converting the incoming request to a proactive conversation.
    Care should be used for bots that operate in a shared hosting environment. 
    The incoming request is immediately completed and many shared hosting environments 
    will mark the bot's process as idle and shut it down.
    """

    file_downloaders: List[InputFileDownloader] = field(default_factory=list)
    """
    Optional. Array of input file download plugins to use. 
    """

    turn_state_factory: Optional[Callable[[], TurnState]] = None
    """
    Optional. Factory function to create the turn state.
    This should return an instance of `TurnState` or a subclass.
    If not provided, the default `TurnState` will be used.
    """

    authorization_handlers: Optional[AuthorizationHandlers] = None
    """
    Optional. Authorization handler for OAuth flows.
    If not provided, no OAuth flows will be supported.
    """
