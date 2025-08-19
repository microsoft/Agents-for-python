import pytest
from unittest.mock import sentinel

from microsoft.agents.hosting.core.storage import MemoryStorage
from microsoft.agents.hosting.core.storage.storage_test_utils import MockStoreItem
from microsoft.agents.hosting.core.app.oauth import (
    FlowState,
    FlowStorageClient,
)

class TestFlowStorageClient:
    
    @pytest.fixture
    def turn_context(self, mocker):
        context = mocker.Mock()
        context.activity.channel_id = "__channel_id"
        context.activity.from_property.id = "__user_id"
        return context
    
    @pytest.fixture
    def storage(self):
        return MemoryStorage()
    
    @pytest.fixture
    def client(self, turn_context, storage):
        return FlowStorageClient(turn_context, storage)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "channel_id, from_property_id",
        [
            ("channel_id", "from_property_id"),
            ("teams_id", "Bob"),
            ("channel", "Alice"),
        ],
    )
    async def test_init_base_key(self, mocker, channel_id, from_property_id):
        context = mocker.Mock()
        context.activity.channel_id = channel_id
        context.activity.from_property.id = from_property_id
        client = FlowStorageClient(context, mocker.Mock())
        assert client.base_key == f"auth/{channel_id}/{from_property_id}/"

    @pytest.mark.asyncio
    async def test_init_fails_without_from_id(self, mocker, storage):
        with pytest.raises(ValueError):
            context = mocker.Mock()
            context.activity.channel_id = "channel_id"
            context.activity.from_property = mocker.Mock(id=None)
            FlowStorageClient(context, storage)

    @pytest.mark.asyncio
    async def test_init_fails_without_channel_id(self, mocker, storage):
        with pytest.raises(ValueError):
            context = mocker.Mock()
            context.activity.channel_id = None
            context.activity.from_property.id = "from_id"
            FlowStorageClient(context, storage)

    @pytest.mark.parametrize(
        "auth_handler_id, expected",
        [
            ("handler", "auth/__channel_id/__user_id/handler"),
            ("auth_handler", "auth/__channel_id/__user_id/auth_handler"),
        ]
    )
    def test_key(self, client, auth_handler_id, expected):
        assert client.key(auth_handler_id) == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id",
        [
            ("handler",),
            ("auth_handler",),
        ]
    )
    async def test_read(self, mocker, turn_context, auth_handler_id):
        storage = mocker.AsyncMock()
        key = f"auth/__channel_id/__user_id/{auth_handler_id}"
        storage.read.return_value = {key: FlowState()}
        client = FlowStorageClient(turn_context, storage)
        res = await client.read(auth_handler_id)
        assert res is storage.read.return_value[key]
        storage.read.assert_called_once_with([f"auth/__channel_id/__user_id/{auth_handler_id}"], FlowState)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id, key",
        [
            ("handler", "auth/__channel_id/__user_id/handler"),
            ("auth_handler", "auth/__channel_id/__user_id/auth_handler"),
        ]
    )
    async def test_write(self, mocker, turn_context, auth_handler_id, key):
        storage = mocker.AsyncMock()
        storage.write.return_value = None
        client = FlowStorageClient(turn_context, storage)
        flow_state = mocker.Mock(spec=FlowState)
        flow_state.auth_handler_id = auth_handler_id
        await client.write(flow_state)
        storage.write.assert_called_once_with({ key: flow_state })

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "auth_handler_id, key",
        [
            ("handler", "auth/__channel_id/__user_id/handler"),
            ("auth_handler", "auth/__channel_id/__user_id/auth_handler"),
        ]
    )
    async def test_delete(self, mocker, turn_context, auth_handler_id, key):
        storage = mocker.AsyncMock()
        storage.delete.return_value = None
        client = FlowStorageClient(turn_context, storage)
        await client.delete(auth_handler_id)
        storage.delete.assert_called_once_with([client.key(auth_handler_id)])

    @pytest.mark.asyncio
    async def test_integration_with_memory_storage(self, turn_context):

        flow_state_alpha = FlowState(auth_handler_id="handler", flow_started=True)
        flow_state_beta = FlowState(auth_handler_id="auth_handler", flow_started=True, user_token="token")

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

        new_flow_state_alpha = FlowState(auth_handler_id="handler")
        flow_state_chi = FlowState(auth_handler_id="chi")
        
        await client.write(new_flow_state_alpha)
        await client.write(flow_state_chi)
        await baseline.write({"auth/__channel_id/__user_id/handler": new_flow_state_alpha.copy()})
        await baseline.write({"auth/__channel_id/__user_id/chi": flow_state_chi.copy()})

        await write_both({"auth/__channel_id/__user_id/handler": new_flow_state_alpha.copy()})
        await write_both({"auth/__channel_id/__user_id/auth_handler": flow_state_beta.copy()})
        await write_both({"other_data": MockStoreItem({"value": "more"})})

        await delete_both(["some_data"])

        await read_check(["auth/__channel_id/__user_id/handler"], target_cls=FlowState)
        await read_check(["auth/__channel_id/__user_id/auth_handler"], target_cls=FlowState)
        await read_check(["auth/__channel_id/__user_id/chi"], target_cls=FlowState)
        await read_check(["other_data"], target_cls=MockStoreItem)
        await read_check(["some_data"], target_cls=MockStoreItem)
