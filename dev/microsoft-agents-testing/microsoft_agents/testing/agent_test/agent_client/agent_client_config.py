from enum import Enum
from dataclasses import dataclass

from microsoft_agents.hosting.core import Connections

class ClientOptionType(Enum):
    EXTERNAL = "external"
    NO_HOST = "no_host"

@dataclass
class TestClientOptions:

    conversation_id: str = "cid"
    user_id: str = "uid"
    locale: str = "en-US"

    sender_sleep: float = 0.1
    receiver_sleep: float = 0.1

    connections: Connections | None = None

class TestClientOptionsBuilder:
    pass