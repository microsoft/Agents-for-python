import pytest

from microsoft_agents.activity import load_configuration_from_env

from microsoft_agents.hosting.core import (
    AgentApplication,
    Storage,
    MemoryStorage,
    Authorization,
    ChannelAdapter,
    TurnState,
    Connections,
)

from tests._common.testing_objects import (
    TestingConnectionManager,
    TestingAdapter,
)


class TestingEnvironment:
    agent_app: AgentApplication
    storage: Storage
    connection_manager: Connections
    adapter: ChannelAdapter
    authorization: Authorization
    env: dict

    def __init__(self, mocker):
        self._mocker = mocker
        self.env = self.get_env()

    def get_env(self):
        return {}


# class SampleEnvironment(TestingEnvironment):

#     def setup_method(self):
#         super().setup_method()

#         self.agents_sdk_config = load_configuration_from_env(self.env)

#         # Create storage and connection manager
#         self.storage = MemoryStorage()
#         self.connection_manager = MsalConnectionManager(**agents_sdk_config)
#         self.adapter = CloudAdapter(connection_manager=self.connection_manager)
#         self.authorization = Authorization(self.storage, self.connection_manager, **agents_sdk_config)

#         self.agent_app = AgentApplication[TurnState](
#             storage=self.storage, adapter=self.adapter, authorization=self.authorization, **agents_sdk_config
#         )


class MockTestingEnvironment(TestingEnvironment):
    def __init__(self, mocker):
        super().__init__(mocker)

        env_dict = self.get_env()

        agents_sdk_config = load_configuration_from_env(env_dict)

        self.storage = MemoryStorage()
        self.connection_manager = TestingConnectionManager()
        self.adapter = TestingAdapter()
        self.authorization = Authorization(
            self.storage, self.connection_manager, **agents_sdk_config
        )

        self.agent_app = AgentApplication[TurnState](
            storage=self.storage,
            adapter=self.adapter,
            authorization=self.authorization,
            **agents_sdk_config
        )
