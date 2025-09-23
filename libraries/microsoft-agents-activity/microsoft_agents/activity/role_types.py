from enum import Enum


class RoleTypes(str, Enum):
    user = "user"
    agent = "bot"
    skill = "skill"
    agent_app_instance = "agentAppInstance"
    agentic_user = "agenticUser"