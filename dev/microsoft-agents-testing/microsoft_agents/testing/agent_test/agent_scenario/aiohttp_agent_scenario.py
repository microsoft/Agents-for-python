class AiohttpAgentScenario:

    def __init__(self):

        self._config = None
        self._storage = MemoryStorage()
        self._connection_manager = MsalConnectionManager(**self._config)
        self._adapter = CloudAdapter(connection_manager=self._connection_manager)
        self._authorization = Authorization(
            self._storage, self._connection_manager, **self._config
        )

    async def _init_agent_application(self):

        self.agent_application = AgentApplication[TurnState](
            storage=self.storage,
            adapter=self.adapter,
            authorization=self.authorization,
            **self.config
        )

    def _fixtures(self):
        base_fixtures = super()._fixtures()
        return base_fixtures + [
            self.agent_application,
            self.turn_state,
            self.storage,
        ]

    @pytest.fixture
    def agent_application(self, test_client):
        return self._scenario.agent_application
    
    @pytest.fixture
    def turn_state(self, test_client):
        return self._scenario.agent_application.turn_state
    
    @pytest.fixture
    def storage(self, test_client):
        return self._scenario.agent_application.storage
    

    @classmethod
    def init_agent(cls, func: Callable[[AgentApplication], Awaitable[None]]
                   ) -> AgentScenario:
        
        class _AgentScenarioImpl(cls):
            async def _init_agent(self):
                await func(self._agent_application)
    
        return _AgentScenarioImpl