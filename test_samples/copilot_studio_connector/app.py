"""
Main application entry point for Copilot Studio Agent Connector sample.
"""

import logging
from aiohttp import web

from microsoft_agents.storage import MemoryStorage
from microsoft_agents.hosting.aiohttp import CloudAdapter
from agent import MyAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def messages(request: web.Request) -> web.Response:
    """
    Handle incoming messages from Azure Bot Service or Copilot Studio.

    :param request: The incoming HTTP request
    :return: HTTP response
    """
    # Get the adapter and agent from the app context
    adapter: CloudAdapter = request.app["adapter"]
    agent: MyAgent = request.app["agent"]

    # Process the incoming activity
    return await adapter.process(request, agent)


def create_app(config_path: str = "appsettings.json") -> web.Application:
    """
    Create and configure the web application.

    :param config_path: Path to configuration file
    :return: Configured aiohttp web application
    """
    # Create agent options from configuration
    # In production, use a proper config loading mechanism
    # options = AgentApplicationOptions.from_configuration(config_path)

    # Create storage (use persistent storage in production)
    storage = MemoryStorage()

    # Create the agent
    agent = MyAgent(options)

    # Create the adapter
    adapter = CloudAdapter(configuration=config_path, storage=storage)

    # Create the web application
    app = web.Application()
    app["adapter"] = adapter
    app["agent"] = agent

    # Register routes
    app.router.add_get("/", lambda _: web.Response(text="Microsoft Agents SDK Sample"))
    app.router.add_post("/api/messages", messages)

    return app


if __name__ == "__main__":
    # Create the app
    app = create_app()

    # Run the web server
    port = 3978
    logger.info(f"Starting Copilot Studio Connector sample on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)
