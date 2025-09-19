from microsoft_agents.activity import (
    load_configuration_from_env
)

from microsoft_agents.hosting.core import (
    AgentApplication,
    Storage,
    MemoryStorage,
    ConnectionManager,
    Authorization,
    ChannelAdapter
)
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter
)

from tests._common.testing_objects import (
    TestingConnectionManager,
    TestingAdapter,
)

class TestingEnvironment:
    app: AgentApplication
    storage: Storage
    connection_manager: ConnectionManager
    adapter: ChannelAdapter
    authorization: Authorization
    env: dict

    def setup_method(self):
        self.env = self.get_env()

    def get_env(self):
        return {}

class SampleEnvironment(TestingEnvironment):

    def setup_method(self):
        super().setup_method()

        self.agents_sdk_config = load_configuration_from_env(self.env)

        # Create storage and connection manager
        self.storage = MemoryStorage()
        self.connection_manager = MsalConnectionManager(**agents_sdk_config)
        self.adapter = CloudAdapter(connection_manager=CONNECTION_MANAGER)
        self.authorization = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

        self.agent_app = AgentApplication[TurnState](
            storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
        )

class MockTestingEnvironment(TestingEnvironment):

    def setup_method(self):
        super().setup_method(env)

        self.agents_sdk_config = load_configuration_from_env(env_dict)

        self.storage = MemoryStorage()
        self.connection_manager = TestingConnectionManager()
        self.adapter = TestingAdapter()
        self.authorization = Authorization(self.storage, self.connection_manager, **agents_sdk_config)

        self.agent_app = AgentApplication[TurnState](
            storage=self.storage, adapter=self.adapter, authorization=self.authorization, **agents_sdk_config
        )
    
