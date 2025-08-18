from microsoft.agents.hosting.core import MemoryStorage

import pytest

from microsoft.agents.hosting.core import (
    Storage,
    FlowStorageClient,
    MockStoreItem,
    FlowState
)

class TestFlowStorageClient:
    
    @pytest.fixture
    def turn_context(self, mocker):
        context = mocker.Mock()
        context.activity.channel_id = "__channel_id"
        context.activity.from_property.id = "__user_id"
        return context
    
    @pytest.fixture
    def client(self, turn_context, storage):
        return FlowStorageClient(turn_context, storage)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mocker, turn_context, storage, channel_id, from_property_id",
        [
            ("mocker", "turn_context", "storage", "channel_id", "from_property_id"),
            ("mocker", "turn_context", "storage", "teams_id", "Bob"),
            ("mocker", "turn_context", "storage", "channel", "Alice"),
        ],
        indirect=["mocker", "turn_context", "storage"]
    )
    async def test_init_base_key(self, mocker, turn_context, storage, channel_id, from_property_id):
        context = mocker.Mock()
        context.activity.channel_id = channel_id
        context.activity.from_property.id = from_property_id
        client = FlowStorageClient(context, storage)
        assert client.base_key == f"auth/{channel_id}/{from_property_id}/"

    async def test_init_fails_without_from_id(self, mocker, storage):
        with pytest.raises(ValueError):
            context = mocker.Mock()
            context.activity.channel_id = "channel_id"
            FlowStorageClient(context, storage)

    async def test_init_fails_without_channel_id(self, mocker, storage):
        with pytest.raises(ValueError):
            context = mocker.Mock()
            context.activity.from_property.id = "from_id"
            FlowStorageClient(context, storage)

    @pytest.mark.parametrize(
        "client, auth_handler_id, expected",
        [
            (client, "handler", "auth/__channel_id/__user_id/handler"),
            (client, "auth_handler", "auth/__channel_id/__user_id/auth_handler"),
        ]
    )
    def test_key(self, client, auth_handler_id, expected):
        assert client.key(auth_handler_id) == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mocker, turn_context storage, client, auth_handler_id",
        [
            (mocker, turn_context, storage, client, "handler"),
            (mocker, turn_context, storage, client, "auth_handler"),
        ]
    )
    async def test_read(self, mocker, turn_context, storage, client, auth_handler_id):
        storage = mocker.AsyncMock()
        storage.read.return_value = sentinel.read_response
        client = FlowStorageClient(turn_context, storage)
        res = await client.read(auth_handler_id)
        assert res == storage.read.return_value
        assert storage.read.called_once_with([f"auth/__channel_id/__user_id/{auth_handler_id}"], FlowState)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mocker, turn_context storage, client, auth_handler_id",
        [
            (mocker, turn_context, storage, client, "handler", "auth/__channel_id/__user_id/handler"),
            (mocker, turn_context, storage, client, "auth_handler", "auth/__channel_id/__user_id/auth_handler"),
        ]
    )
    async def test_write(self, mocker, turn_context, storage, client, auth_handler_id, key, flow_state):
        storage = mocker.AsyncMock()
        storage.write.return_value = None
        client = FlowStorageClient(turn_context, storage)
        flow_state = mocker.Mock(spec=FlowState)
        flow_state.id = auth_handler_id
        await client.write(flow_state)
        assert storage.write.called_once_with({ key: flow_state })

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "mocker, turn_context storage, client, auth_handler_id",
        [
            (mocker, turn_context, storage, client, "handler", "auth/__channel_id/__user_id/handler"),
            (mocker, turn_context, storage, client, "auth_handler", "auth/__channel_id/__user_id/auth_handler"),
        ]
    )
    async def test_delete(self, mocker, turn_context, storage, client, auth_handler_id):
        storage = mocker.AsyncMock()
        storage.write.return_value = None
        client = FlowStorageClient(turn_context, storage)
        await client.delete(auth_handler_id)
        assert storage.write.called_once_with([auth_handler_id])

    async def test_integration_with_memory_storage(self, turn_context):

        flow_state_alpha = FlowState(flow_id="handler", flow_started=True)
        flow_state_beta = FlowState(flow_id="auth_handler", flow_started=True, user_token="token")

        storage = MemoryStorage({
            "some_data": MockStoreItem({"value": "test"}),
            "auth/__channel_id/__user_id/handler": flow_state_alpha,
            "auth/__channel_id/__user_id/auth_handler": flow_state_beta,
        })
        baseline = MemoryStorage({
            "some_data": MockStoreItem({"value": "test"}),
            "auth/__channel_id/__user_id/handler": flow_state_alpha,
            "auth/__channel_id/__user_id/auth_handler": flow_state_beta,
        })

        # helpers
        async def read_check(*args, **kwargs):
            res_storage = await storage.read(*args, **kwargs)
            res_baseline = await baseline.read(*args, **kwargs)
            assert res_storage == res_baseline

        async def write_both(*args, **kwargs):
            await storage.write(*args, **kwargs)
            await baseline.write(*args, **kwargs)

        async def delete_both(*args, **kwargs):
            await storage.delete(*args, **kwargs)
            await baseline.delete(*args, **kwargs)

        client = FlowStorageClient(turn_context, storage)

        new_flow_state_alpha = FlowState(flow_id="handler")
        flow_state_chi = FlowState(flow_id="chi")
        
        await client.write(new_flow_state_alpha)
        await client.write(flow_state_chi)
        baseline.write({"auth/__channel_id/__user_id/handler": new_flow_state_alpha.copy()})
        baseline.write({"auth/__channel_id/__user_id/chi": flow_state_chi.copy()})

        write_both({"auth/__channel_id/__user_id/handler": new_flow_state_alpha.copy()})
        write_both({"auth/__channel_id/__user_id/auth_handler": flow_state_beta.copy()})
        write_both({"other_data": MockStoreItem({"value": "more"}).copy()})

        delete_both(["some_data"])

        assert read_check(["auth/__channel_id/__user_id/handler"], FlowState)
        assert read_check(["auth/__channel_id/__user_id/auth_handler"], FlowState)
        assert read_check(["auth/__channel_id/__user_id/chi"], FlowState)
        assert read_check(["other_data"], MockStoreItem)
        assert read_check(["some_data"], MockStoreItem)
