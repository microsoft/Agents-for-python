from dataclasses import dataclass

from microsoft_agents.hosting.core import Connections

@dataclass
class TestClientOptions:

    conversation_id: str = "cid"
    user_id: str = "uid"
    locale: str = "en-US"

    connections: Connections | None = None  