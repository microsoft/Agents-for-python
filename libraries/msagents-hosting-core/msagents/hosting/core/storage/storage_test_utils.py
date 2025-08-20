import pytest
import gc
from copy import deepcopy
from abc import ABC
from typing import Any

from .storage import Storage
from .store_item import StoreItem
from ._type_aliases import JSON
from .memory_storage import MemoryStorage


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


def my_deepcopy(original):
    """Deep copy an object, including StoreItem instances."""

    iter_obj = None
    if isinstance(original, list):
        iter_obj = enumerate(original)
    elif isinstance(original, dict):
        iter_obj = original.items()
    elif isinstance(original, MockStoreItem):
        return original.deepcopy()
    else:
        return deepcopy(original)

    obj = {} if isinstance(original, dict) else ([None] * len(original))
    for key, value in iter_obj:
        obj[key] = my_deepcopy(value)
    return obj


def subsets(lst, n=-1):
    """Generate all subsets of a list up to length n. If n is -1, all subsets are generated.

    Only contiguous subsets are generated.
    """
    if n < 0:
        n = len(lst)
    subsets = []
    for i in range(len(lst) + 1):
        for j in range(0, i):
            if 1 <= i - j <= n:
                subsets.append(lst[j:i])
    return subsets


# bootstrapping class to compare against
# if this class is correct, then the tests are correct
class StorageBaseline(Storage):
    """ "A simple in-memory storage implementation for testing purposes."""

    def __init__(self, initial_data: dict = None):
        self._memory = deepcopy(initial_data) or {}
        self._key_history = set(initial_data.keys()) if initial_data else set()

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


class StorageTestsCommon(ABC):
    """Common fixtures for Storage implementations."""

    KEY_LIST = [
        "f",
        "a!0dslfj",
        "\\?/#\t\n\r*",
        "527",
        "test.txt",
        "_-__--",
        "VAR",
        "None",
        "multi word key",
    ]

    READ_KEY_LIST = KEY_LIST + (["5", "20", "100", "nonexistent_key", "-"])

    STATE_LIST = [
        {key: MockStoreItem({"id": key, "value": f"value{key}"}) for key in subset}
        for subset in subsets(KEY_LIST, 3)
        if len(subset) == 3
    ]

    @pytest.fixture(params=[dict()] + STATE_LIST)
    def initial_state(self, request):
        return request.param

    @pytest.fixture(params=KEY_LIST)
    def key(self, request):
        return request.param

    @pytest.fixture(
        params=[subset for subset in subsets(READ_KEY_LIST, 2) if len(subset) == 2]
    )
    def keys(self, request):
        return request.param

    @pytest.fixture(params=subsets(KEY_LIST, 2))
    def changes(self, request):
        changes_obj = {}
        keys = request.param
        changes_obj["new_key"] = MockStoreItemB(
            {"field": "new_value_for_new_key"}, True
        )
        for i, key in enumerate(keys):
            if i % 2 == 0:
                changes_obj[key] = MockStoreItemB(
                    {"data": f"value{key}"}, (i // 2) % 2 == 0
                )
            else:
                changes_obj[key] = MockStoreItem(
                    {"id": key, "value": f"new_value_for_{key}"}
                )
        changes_obj["new_key_2"] = MockStoreItem({"field": "new_value_for_new_key_2"})
        return changes_obj


class CRUDStorageTests(StorageTestsCommon):
    """Tests for Storage implementations that support CRUD operations.

    To use, subclass and implement the `storage` method.
    """

    async def storage(self, initial_data=None, existing=False) -> Storage:
        """Return a Storage instance to be tested.
        :param initial_data: The initial data to populate the storage with.
        :param existing: If True, the storage instance should connect to an existing store.
        """
        raise NotImplementedError("Subclasses must implement this")

    @pytest.mark.asyncio
    async def test_read_individual(self, initial_state, key):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        expected = baseline_storage.read([key])
        actual = await storage.read([key], target_cls=MockStoreItem)
        assert actual == expected
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_read(self, initial_state, keys):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        expected = baseline_storage.read(keys)
        actual = await storage.read(keys, target_cls=MockStoreItem)
        assert actual == expected
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_read_missing_key(self, initial_state):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        keys = ["5", "20", "100", "nonexistent_key", "-"]
        expected = baseline_storage.read(keys)
        actual = await storage.read(keys, target_cls=MockStoreItem)
        assert actual == expected
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_read_errors(self, initial_state):
        initial_state_copy = my_deepcopy(initial_state)
        storage = await self.storage(initial_state)
        with pytest.raises(ValueError):
            await storage.read([], target_cls=MockStoreItem)
        with pytest.raises(ValueError):
            await storage.read(None, target_cls=MockStoreItem)
        with pytest.raises(ValueError):
            await storage.read([""], target_cls=MockStoreItem)
        with pytest.raises(ValueError):
            await storage.read(["key"], target_cls=None)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_write_individual(self, initial_state, key):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        change = {key: MockStoreItem({key: f"new_value_for_{key}!"})}
        baseline_storage.write(change)
        await storage.write(change)
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_write_individual_different_target_cls(self, initial_state, key):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        change = {
            key: MockStoreItemB({key: f"new_value_for_{key}!"}, other_field=False)
        }
        baseline_storage.write(change)
        await storage.write(change)
        assert await baseline_storage.equals(storage)
        change = {key: MockStoreItemB({key: f"new_{key}"}, other_field=True)}
        baseline_storage.write(change)
        await storage.write(change)
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_write_same_values(self, initial_state):
        if not initial_state:
            return
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        changes = {key: value for key, value in initial_state.items()}
        baseline_storage.write(changes)
        await storage.write(changes)
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_write(self, initial_state, changes):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        baseline_storage.write(changes)
        await storage.write(changes)
        assert await baseline_storage.equals(storage)
        baseline_storage.write(initial_state)
        if initial_state:
            await storage.write(initial_state)
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_write_errors(self, initial_state):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        with pytest.raises(ValueError):
            await storage.write({})
        with pytest.raises(ValueError):
            await storage.write(None)
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_delete_individual(self, initial_state, key):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        baseline_storage.delete([key])
        await storage.delete([key])
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_delete(self, initial_state, keys):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        baseline_storage.delete(keys)
        await storage.delete(keys)
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_delete_missing_key(self, initial_state):
        initial_state_copy = my_deepcopy(initial_state)
        baseline_storage = StorageBaseline(initial_state)
        storage = await self.storage(initial_state)
        keys = ["5", "20", "100", "nonexistent_key", "-"]
        baseline_storage.delete(keys)
        await storage.delete(keys)
        assert await baseline_storage.equals(storage)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_delete_errors(self, initial_state):
        initial_state_copy = my_deepcopy(initial_state)
        storage = await self.storage(initial_state)
        with pytest.raises(ValueError):
            await storage.read([])
        with pytest.raises(ValueError):
            await storage.read(None)
        assert initial_state == initial_state_copy

    @pytest.mark.asyncio
    async def test_flow(self):
        baseline_storage = StorageBaseline()
        storage = await self.storage()

        res = await storage.read(["key"], target_cls=MockStoreItemB)
        assert len(res) == 0
        assert await baseline_storage.equals(storage)

        changes = {
            "key_a": MockStoreItem({"id": "key_a", "value": "value_a"}),
            "key_b": MockStoreItemB(
                {"id": "key_b", "value": "value_b"}, other_field=False
            ),
        }
        changes_copy = my_deepcopy(changes)

        baseline_storage.write(changes)
        await storage.write(changes)

        assert (
            await storage.read(["key_a"], target_cls=MockStoreItem)
        ) == baseline_storage.read(["key_a"])
        assert (
            await storage.read(["key_b"], target_cls=MockStoreItemB)
        ) == baseline_storage.read(["key_b"])
        assert changes_copy == changes

        baseline_storage.delete(["key_a"])
        await storage.delete(["key_a"])
        assert await baseline_storage.equals(storage)

        change = {"key_b": MockStoreItem({"id": "key_b", "value": "new_value_b"})}
        baseline_storage.write(change)
        await storage.write(change)

        assert await baseline_storage.equals(storage)
        assert (
            await storage.read(["key_b"], target_cls=MockStoreItem)
        ) == baseline_storage.read(["key_b"])

        with pytest.raises(ValueError):
            await storage.read([], target_cls=MockStoreItem)
        with pytest.raises(ValueError):
            await storage.read(["key_b"], target_cls=None)

        change = {
            "key_c": MockStoreItemB(
                {"id": "key_c", "value": "value_c"}, other_field=True
            )
        }
        baseline_storage.write(change)
        await storage.write(change)
        assert (
            await storage.read(["key_a", "key_b"], target_cls=MockStoreItem)
        ) == baseline_storage.read(["key_a", "key_b"])
        assert (
            await storage.read(["key_a", "key_c"], target_cls=MockStoreItemB)
        ) == baseline_storage.read(["key_a", "key_c"])

        item_parent_class = (await storage.read(["key_c"], target_cls=MockStoreItem))[
            "key_c"
        ]
        item_child_class = (await storage.read(["key_c"], target_cls=MockStoreItemB))[
            "key_c"
        ]
        assert item_parent_class.data[0] == item_child_class.data
        assert item_child_class.other_field == True

        with pytest.raises(ValueError):
            await storage.write({})
        with pytest.raises(Exception):
            await storage.read(["key_b"], target_cls=MockStoreItemB)
        assert await baseline_storage.equals(storage)

        if not isinstance(storage, MemoryStorage):
            # if not memory storage, then items should persist
            del storage
            gc.collect()
            storage_alt = await self.storage(existing=True)
            assert await baseline_storage.equals(storage_alt)


class QuickCRUDStorageTests(CRUDStorageTests):
    """Reduced set of permutations for quicker tests. Useful for debugging."""

    KEY_LIST = ["\\?/#\t\n\r*", "test.txt"]

    READ_KEY_LIST = KEY_LIST + ["nonexistent_key"]

    STATE_LIST = [
        {key: MockStoreItem({"id": key, "value": f"value{key}"}) for key in KEY_LIST}
    ]

    @pytest.fixture(params=STATE_LIST)
    def initial_state(self, request):
        return request.param

    @pytest.fixture(params=KEY_LIST)
    def key(self, request):
        return request.param

    @pytest.fixture(params=[KEY_LIST])
    def keys(self, request):
        return request.param

    @pytest.fixture(params=subsets(KEY_LIST, 2))
    def changes(self, request):
        changes_obj = {}
        keys = request.param
        changes_obj["new_key"] = MockStoreItemB(
            {"field": "new_value_for_new_key"}, True
        )
        for i, key in enumerate(keys):
            if i % 2 == 0:
                changes_obj[key] = MockStoreItemB(
                    {"data": f"value{key}"}, (i // 2) % 2 == 0
                )
            else:
                changes_obj[key] = MockStoreItem(
                    {"id": key, "value": f"new_value_for_{key}"}
                )
        changes_obj["new_key_2"] = MockStoreItem({"field": "new_value_for_new_key_2"})
        return changes_obj


def debug_print(*args):
    """Print debug information clearly separated in the console."""
    print("\n" * 2)
    print("--- DEBUG ---")
    for arg in args:
        print("\n" * 2)
        print(arg)
    print("\n" * 2)
    print("--- ----- ---")
    print("\n" * 2)
