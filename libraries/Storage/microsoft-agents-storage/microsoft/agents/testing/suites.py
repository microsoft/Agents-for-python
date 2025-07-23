
class StorageTestSuiteBase(ABC):

    @pytest.fixture
    def storate_pair(self, initial_state) -> tuple[Storage, StorageBaseline]:
        pass

    @pytest.fixture(params=["test_key", "missing_key", "!#%*#", "another-key.txt"])
    def read_item_key(self, request) -> str:
        return request.param
    
    @pytest.fixture
    def long_key(self) -> str:
        return "a" * 255

    async def check_unchanged(self, promise: Awaitable, storage_state):
        state_before = storage_state.state()
        await promise
        state_after = storage_state.state()
        assert StorageState.compare(state_before, state_after)

    async def check_props_unchanged(self, promise: Awaitable, storage_state):
        state_before = storage_state.state()
        res = await promise
        state_after = storage_state.state()
        assert StorageState.compare(state_before, state_after)
        return res

    async def check_keys(self, promise: Awaitable, keys: list[str]):
        await promise


class ItemStorageMock(ItemStorageBase):

    def read_raw_item(self, storage_and_baseline_pair):

        storage_and_baseline_pair
        
        
    def write_item(self, item: StoreItem):
        pass

    def delete_item(self, key: str):
        pass

class AutoStorageMock(ItemStorageMock, AutoStorageBase):

    def read_raw_item(self, key: str):
        pass
        
    def write_item(self, item: StoreItem):
        pass

    def delete_item(self, key: str):
        pass