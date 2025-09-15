from agents import Agent
from microsoft_agents.activity import AgentsModel
from typing import Optional, Any

from .messaging_extension_result import MessagingExtensionResult

class MessagingExtensionResponse(AgentsModel):
    compose_extension: Optional[MessagingExtensionResult] = None
    cache_info : Optional[Any] = None # robrandao: TODO