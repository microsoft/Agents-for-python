from microsoft_agents.testing import AiohttpAgentScenario


async def create_app(agent_application: AgentApplication):
    pass

scenario = AiohttpAgentScenario(create_app)