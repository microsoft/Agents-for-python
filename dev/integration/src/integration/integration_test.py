from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Generic, Protocol

import pytest

from microsoft_agents.hosting.core import (
    AgentApplication,
    ChannelAdapter,
    Connections
)

from ..samples import Sample

class SampleFactory(Protocol):

    def __call__(self, *args, **kwargs) -> Awaitable[Sample]:
        ...

def integration_suite_factory(
    sample_factory: Callable[[...], Awaitable[Sample]]
):
    class IntegrationTestSuite:
        sample: Sample

        def setup_method(self, mocker):
            self.sample = sample_factory(mocker=mocker)

        @pytest.fixture
        def agent_application(self) -> AgentApplication:
            return self.sample.agent_application
        
        @pytest.fixture
        def adapter(self) -> ChannelAdapter:
            return self.sample.adapter
        
        @pytest.fixture
        def connections(self) -> Connections:
            return self.sample.connections

    return IntegrationTestSuite