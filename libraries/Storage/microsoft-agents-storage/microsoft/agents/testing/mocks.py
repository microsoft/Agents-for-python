from typing import Any

from microsoft.agents.storage.store_item import StoreItem
from microsoft.agents.storage._type_aliases import JSON

from .utils import my_deepcopy

class MockStoreItem(StoreItem):
    """Test implementation of StoreItem for testing purposes"""

    def __init__(self, data: dict[str, Any] = None):
        self.data = data or {}

    def store_item_to_json(self) -> JSON:
        return self.data

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> "MockStoreItem":
        return MockStoreItem(json_data)

    def __eq__(self, other):
        if not isinstance(other, MockStoreItem):
            return False
        return self.data == other.data

    def __repr__(self):
        return f"MockStoreItem({self.data})"

    def deepcopy(self):
        return MockStoreItem(my_deepcopy(self.data))


class MockStoreItemB(MockStoreItem):
    """Another test implementation of StoreItem for testing purposes"""

    def __init__(self, data: dict[str, Any] = None, other_field: bool = True):
        super().__init__(data or {})
        self.other_field = other_field

    def store_item_to_json(self) -> JSON:
        return [self.data, self.other_field]

    @staticmethod
    def from_json_to_store_item(json_data: JSON) -> "MockStoreItem":
        return MockStoreItemB(json_data[0], json_data[1])

    def __eq__(self, other):
        if not isinstance(other, MockStoreItemB):
            return False
        return self.data == other.data and self.other_field == other.other_field

    def deepcopy(self):
        return MockStoreItemB(my_deepcopy(self.data), self.other_field)
    
class StorageBaseline(ABC):

    def __init__(self, initial_data: dict = None):
        self._memory = deepcopy(initial_data) or {}
        self._key_history = set(initial_data.keys()) if initial_data else set()

    @abstractmethod
    def get_properties(self) -> JSON:
        pass

    @abstractmethod
    def get_items(self) -> dict[str, JSON]:
        pass

    @staticmethod
    def compare(self, a: "StorageState", b: "StorageState"):
        pass

    def read(self, keys: list[str]) -> dict[str, Any]:
        self._key_history.update(keys)
        return {key: self._memory.get(key) for key in keys if key in self._memory}

    def write(self, changes: dict[str, Any]) -> None:
        self._key_history.update(changes.keys())
        self._memory.update(changes)

    def delete(self, keys: list[str]) -> None:
        self._key_history.update(keys)
        for key in keys:
            if key in self._memory:
                del self._memory[key]

    async def equals(self, other) -> bool:
        """
        Compare the items for all keys seen by this mock instance.

        Note:
        This is an extra safety measure, and I've made the
        executive decision to not test this method itself
        because passing tests with calls to this method
        is also dependent on the correctness of other
        aspects, based on the other assertions in the tests.
        """
        for key in self._key_history:
            if key not in self._memory:
                if len(await other.read([key], target_cls=MockStoreItem)) > 0:
                    return False  # key should not exist in other
                continue

            # key exists in baseline instance, so let's see if the values match
            item = self._memory.get(key, None)
            target_cls = type(item)
            res = await other.read([key], target_cls=target_cls)

            if key not in res or item != res[key]:
                return False
        return True
    
    @asynccontextmanager
    async def check_unchanged(self, promise: Awaitable, storage_state):
        state_before = storage_state.state()
        yield await promise
        state_after = storage_state.state()
        assert StorageState.compare(state_before, state_after)

    @asynccontextmanager
    async def check_props_unchanged(self, promise: Awaitable, check_keys=False):
        if check_keys:
            keys_before = self.keys()
        props_before = storage_state.state()
        res = await promise
        yield res
        props_after = storage_state.state()
        assert self.compare(props_before, props_after)
        if check_keys:
            keys_after = self.keys()
            assert keys_before == keys_after