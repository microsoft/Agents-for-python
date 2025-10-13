import pytest

from microsoft_agents.hosting.core.storage import MemoryStorage
from microsoft_agents.hosting.core._oauth import _FlowState, _FlowStorageClient

from tests._common.storage.utils import MockStoreItem
from tests._common.data import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()


class TestStorageNamespace:
    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def client(self, storage):
        return _FlowStorageClient(DEFAULTS.channel_id, DEFAULTS.user_id, storage)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "channel_id, user_id",
        [
            ("channel_id", "user_id"),
            ("teams_id", "Bob"),
            ("channel", "Alice"),
        ],
    )
    async def test_init_base_key(self, mocker, channel_id, user_id):
        client = _FlowStorageClient(channel_id, user_id, mocker.Mock())
        assert client.base_key == f"auth/{channel_id}/{user_id}/"

    @pytest.mark.asyncio
    async def test_init_fails_without_user_id(self, storage):
        with pytest.raises(ValueError):
            _FlowStorageClient(DEFAULTS.channel_id, "", storage)

    @pytest.mark.asyncio
    async def test_init_fails_without_channel_id(self, storage):
        with pytest.raises(ValueError):
            _FlowStorageClient("", DEFAULTS.user_id, storage)

    @pytest.mark.parametrize(
        "auth_handler_id, expected",
        [
            ("handler", "auth/__channel_id/__user_id/handler"),
            ("auth_handler", "auth/__channel_id/__user_id/auth_handler"),
        ],
    )
    def test_key(self, client, auth_handler_id, expected):
        assert client.key(auth_handler_id) == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize("auth_handler_id", ["handler", "auth_handler"])
    async def test_read(self, mocker, auth_handler_id):
        storage = mocker.AsyncMock()
        key = f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/{auth_handler_id}"
        storage.read.return_value = {key: _FlowState()}
        client = _FlowStorageClient(DEFAULTS.channel_id, DEFAULTS.user_id, storage)
        res = await client.read(auth_handler_id)
        assert res is storage.read.return_value[key]
        storage.read.assert_called_once_with(
            [client.key(auth_handler_id)], target_cls=_FlowState
        )

    @pytest.mark.asyncio
    async def test_read_missing(self, mocker):
        storage = mocker.AsyncMock()
        storage.read.return_value = {}
        client = _FlowStorageClient("__channel_id", "__user_id", storage)
        res = await client.read("non_existent_handler")
        assert res is None
        storage.read.assert_called_once_with(
            [client.key("non_existent_handler")], target_cls=_FlowState
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("auth_handler_id", ["handler", "auth_handler"])
    async def test_write(self, mocker, auth_handler_id):
        storage = mocker.AsyncMock()
        storage.write.return_value = None
        client = _FlowStorageClient(DEFAULTS.channel_id, DEFAULTS.user_id, storage)
        flow_state = mocker.Mock(spec=_FlowState)
        flow_state.auth_handler_id = auth_handler_id
        await client.write(flow_state)
        storage.write.assert_called_once_with({client.key(auth_handler_id): flow_state})

    @pytest.mark.asyncio
    @pytest.mark.parametrize("auth_handler_id", ["handler", "auth_handler"])
    async def test_delete(self, mocker, auth_handler_id):
        storage = mocker.AsyncMock()
        storage.delete.return_value = None
        client = _FlowStorageClient(DEFAULTS.channel_id, DEFAULTS.user_id, storage)
        await client.delete(auth_handler_id)
        storage.delete.assert_called_once_with([client.key(auth_handler_id)])

    @pytest.mark.asyncio
    async def test_integration_with_memory_storage(self):

        flow_state_alpha = _FlowState(auth_handler_id="handler")
        flow_state_beta = _FlowState(auth_handler_id="auth_handler")

        storage = MemoryStorage(
            {
                "some_data": MockStoreItem({"value": "test"}),
                f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/handler": flow_state_alpha,
                f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/auth_handler": flow_state_beta,
            }
        )
        baseline = MemoryStorage(
            {
                "some_data": MockStoreItem({"value": "test"}),
                f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/handler": flow_state_alpha,
                f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/auth_handler": flow_state_beta,
            }
        )

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

        client = _FlowStorageClient(DEFAULTS.channel_id, DEFAULTS.user_id, storage)

        new_flow_state_alpha = _FlowState(auth_handler_id="handler")
        flow_state_chi = _FlowState(auth_handler_id="chi")

        await client.write(new_flow_state_alpha)
        await client.write(flow_state_chi)
        await baseline.write(
            {
                f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/handler": new_flow_state_alpha.model_copy()
            }
        )
        await baseline.write(
            {
                f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/chi": flow_state_chi.model_copy()
            }
        )

        await write_both(
            {
                f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/handler": new_flow_state_alpha.model_copy()
            }
        )
        await write_both(
            {
                f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/auth_handler": flow_state_beta.model_copy()
            }
        )
        await write_both({"other_data": MockStoreItem({"value": "more"})})

        await delete_both(["some_data"])

        await read_check(
            [f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/handler"],
            target_cls=_FlowState,
        )
        await read_check(
            [f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/auth_handler"],
            target_cls=_FlowState,
        )
        await read_check(
            [f"auth/{DEFAULTS.channel_id}/{DEFAULTS.user_id}/chi"],
            target_cls=_FlowState,
        )
        await read_check(["other_data"], target_cls=MockStoreItem)
        await read_check(["some_data"], target_cls=MockStoreItem)
