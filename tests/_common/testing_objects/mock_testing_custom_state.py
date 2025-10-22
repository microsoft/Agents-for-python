from microsoft_agents.hosting.core import AgentState, Storage, StoreItem, TurnContext


class MockTestingCustomState(AgentState):
    """Custom state implementation for testing."""

    def __init__(self, storage: Storage, namespace: str = ""):
        self.namespace = namespace
        super().__init__(storage, "MockCustomState")

    def get_storage_key(
        self, turn_context: TurnContext, *, target_cls: type[StoreItem] = None
    ) -> str:
        """
        Returns the storage key for the custom state.
        """
        conversation_id = turn_context.activity.conversation.id
        if not conversation_id:
            raise ValueError("Invalid activity: missing conversation.id")

        key = f"custom/{conversation_id}"
        if self.namespace:
            key = f"{self.namespace}/{key}"
        return key
