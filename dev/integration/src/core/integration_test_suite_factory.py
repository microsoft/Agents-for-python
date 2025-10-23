from typing import Optional

import pytest

from microsoft_agents.hosting.core import (
    AgentApplication,
    ChannelAdapter,
    Connections
)

from .environment import Environment, create_aiohttp_env
from .sample import Sample

def integration_test_suite_factory(
    sample_cls: type[Sample],
    environment: Optional[Environment] = None
):
    """Factory function to create an integration test suite for a given sample application.
    
    :param environment: The environment to use for the sample application.
    :param sample_cls: The sample class to create the test suite for.
    :return: An integration test suite class.
    """

    if not environment:
        environment = create_aiohttp_env()
    
    class IntegrationTestSuite:
        """Integration test suite for a given sample application."""
        sample: Sample

        async def setup_method(self, mocker):
            """Set up the test suite with the sample application."""
            self.sample = sample_cls(environment, mocker=mocker)
            await self.sample.init_app()
            await self.sample.runner.start()

        async def teardown_method(self):
            """Tear down the test suite and clean up resources."""
            await self.sample.runner.stop()

        @pytest.fixture
        def agent_application(self) -> AgentApplication:
            """Get the agent application for the test suite."""
            return self.sample.env.agent_application
        
        @pytest.fixture
        def adapter(self) -> ChannelAdapter:
            """Get the channel adapter for the test suite."""
            return self.sample.env.adapter
        
        @pytest.fixture
        def connections(self) -> Connections:
            """Get the connections for the test suite."""
            return self.sample.env.connections

    return IntegrationTestSuite