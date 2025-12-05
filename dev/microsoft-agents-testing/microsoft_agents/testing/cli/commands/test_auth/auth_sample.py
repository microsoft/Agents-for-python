# import os

# from dotenv import load_dotenv

# from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

# from microsoft_agents.testing.integration.core.sample import Sample


# def create_auth_route(auth_handler_id: str, agent: AgentApplication):
#     def dynamic_function(context: TurnContext, state: TurnState):
#         token = await agent.auth.get_token(context, state, auth_handler_id)

#         return f"Hello from {auth_handler_id}! Token: {token}"

#     dynamic_function.__name__ = f"auth_route_{auth_handler_id}".lower()
#     return dynamic_function


# class QuickstartSample(Sample):
#     """A quickstart sample implementation."""

#     @classmethod
#     async def get_config(cls) -> dict:
#         """Retrieve the configuration for the sample."""
#         load_dotenv("./src/tests/.env")
#         return dict(os.environ)

#     async def init_app(self):
#         """Initialize the application for the quickstart sample."""

#         app: AgentApplication[TurnState] = self.env.agent_application

#         for auth_handler in app.config.authentication_handlers:
#             app.message(
#                 auth_handler.name.lower(),
#                 create_auth_route(auth_handler.name),
#                 auth_handlers=[auth_handler.name],
#             )
