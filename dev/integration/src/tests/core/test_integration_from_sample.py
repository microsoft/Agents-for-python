import pytest
import asyncio
from copy import copy

from src.core import (
    ApplicationRunner,
    Environment,
    integration,
    IntegrationFixtures,
    Sample
)

from ._common import SimpleRunner, OtherSimpleRunner

class SimpleEnvironment(Environment):
    """A simple implementation of the Environment for testing."""
    
    async def init_env(self, environ_config: dict) -> None:
        self.config = environ_config
        # Initialize other components as needed

    def create_runner(self) -> ApplicationRunner:
        return SimpleRunner(copy(self.config))

class SimpleSample(Sample):
    """A simple implementation of the Sample for testing."""

    def __init__(self, environment: Environment, **kwargs):
        super().__init__(environment, **kwargs)
        self.data = kwargs.get("data", "default_data")
        self.other_data = None
    
    @classmethod
    async def get_config(cls) -> dict:
        return {"sample_key": "sample_value"}
    
    async def init_app(self):
        await asyncio.sleep(0.1)  # Simulate some initialization delay
        self.other_data = len(self.env.config)
        
@integration(sample=SimpleSample, environment=SimpleEnvironment)
class TestIntegrationFromSample(IntegrationFixtures):
    
    @pytest.mark.asyncio
    async def test_sample_integration(self, sample, environment):
        """Test the integration of SimpleSample with SimpleEnvironment."""

        assert environment.config == {
            "sample_key": "sample_value"
        }

        assert sample.env is environment
        assert sample.data == "default_data"
        assert sample.other_data == 1

        runner = environment.create_runner()
        assert runner.app == {"running": True}