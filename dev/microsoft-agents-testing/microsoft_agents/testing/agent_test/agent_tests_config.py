from __future__ import annotations

class AgentTestConfig:
    
    pass

class AgentTestsConfigBuilder:

    def __init__(self):
        pass

    def service_url(self, url: str) -> AgentTestsConfigBuilder:
        return self

    def build(self) -> AgentTestConfig:
        return AgentTestConfig()