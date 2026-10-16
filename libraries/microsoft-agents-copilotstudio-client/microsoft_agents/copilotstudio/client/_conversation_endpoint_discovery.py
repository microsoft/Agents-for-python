# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Literal, Optional
from urllib.parse import quote, urlsplit, urlunsplit

from .connection_settings import ConnectionSettings
from .errors import copilot_studio_errors
from .power_platform_environment import PowerPlatformEnvironment

ConversationOperation = Literal["createConversation", "executeTurn", "subscribe"]
_CONVERSATION_ID = "{conversationId}"


def get_discovery_url(settings: ConnectionSettings) -> str:
    url = urlsplit(PowerPlatformEnvironment.get_copilot_studio_connection_url(settings))
    return urlunsplit(
        (
            url.scheme,
            url.netloc,
            f"/copilotstudio/agents/{quote(settings.agent_identifier, safe='')}/conversation-endpoints",
            "",
            "",
        )
    )


def _validate_url(
    value: object, discovery_url: str, requires_conversation_id: bool
) -> str:
    error = str(copilot_studio_errors.InvalidDiscoveryOperationUrl)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(error)

    remainder = value.replace(_CONVERSATION_ID, "")
    if (
        requires_conversation_id != (_CONVERSATION_ID in value)
        or "{" in remainder
        or "}" in remainder
        or "\\" in value
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        raise ValueError(error)

    try:
        discovery = urlsplit(discovery_url)
        url = urlsplit(value.replace(_CONVERSATION_ID, "conversation"))
        host = discovery.hostname or ""
        suffix_index = host.find(".environment.")
        suffix = host[suffix_index:] if suffix_index >= 0 else "." + host
        valid = (
            url.scheme == "https"
            and (url.port if url.port is not None else 443)
            == (discovery.port if discovery.port is not None else 443)
            and bool(url.hostname)
            and url.hostname.endswith(suffix)
            and url.username is None
            and url.password is None
            and not url.fragment
        )
    except ValueError as exc:
        raise ValueError(error) from exc
    if not valid:
        raise ValueError(error)
    return value


@dataclass(frozen=True)
class ConversationEndpoints:
    create_conversation: str
    execute_turn: str
    continue_turn: str
    subscribe: Optional[str]

    @classmethod
    def from_response(cls, data: object, discovery_url: str) -> "ConversationEndpoints":
        if not isinstance(data, dict):
            raise ValueError(str(copilot_studio_errors.InvalidDiscoveryResponse))

        return cls(
            create_conversation=_validate_url(
                data.get("createConversation"), discovery_url, False
            ),
            execute_turn=_validate_url(data.get("executeTurn"), discovery_url, True),
            continue_turn=_validate_url(data.get("continueTurn"), discovery_url, True),
            subscribe=(
                _validate_url(data["subscribe"], discovery_url, True)
                if data.get("subscribe") is not None
                else None
            ),
        )

    def get_url(
        self, operation: ConversationOperation, conversation_id: Optional[str] = None
    ) -> str:
        if operation == "createConversation":
            return self.create_conversation
        if not conversation_id:
            raise ValueError(str(copilot_studio_errors.DiscoveryConversationIdRequired))
        url = self.execute_turn if operation == "executeTurn" else self.subscribe
        if url is None:
            raise NotImplementedError(
                str(copilot_studio_errors.DiscoverySubscribeNotSupported)
            )
        return url.replace(_CONVERSATION_ID, quote(conversation_id, safe=""))
