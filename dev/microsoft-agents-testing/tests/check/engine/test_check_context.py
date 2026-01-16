import pytest

from microsoft_agents.testing.check.engine.check_context import CheckContext
from microsoft_agents.testing.check.engine.types import SafeObject, resolve


class TestCheckContextInitialization:
    """Test CheckContext initialization."""

    def test_init_with_primitive_values(self):
        """Test initialization with primitive actual and baseline values."""
        actual = SafeObject(42)
        baseline = 100
        
        ctx = CheckContext(actual=actual, baseline=baseline)
        
        assert ctx.actual is actual
        assert ctx.baseline == baseline
        assert ctx.path == []
        assert ctx.root_actual is actual
        assert ctx.root_baseline is baseline

    def test_init_with_dict_values(self):
        """Test initialization with dictionary actual and baseline values."""
        actual_data = {"name": "John", "age": 30}
        baseline_data = {"name": "Jane", "age": 25}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        
        assert resolve(ctx.actual) == actual_data
        assert ctx.baseline == baseline_data
        assert ctx.path == []

    def test_init_with_nested_dict_values(self):
        """Test initialization with nested dictionary values."""
        actual_data = {"user": {"profile": {"name": "John"}}}
        baseline_data = {"user": {"profile": {"name": "Jane"}}}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        
        assert resolve(ctx.actual) == actual_data
        assert ctx.baseline == baseline_data

    def test_init_with_list_values(self):
        """Test initialization with list values."""
        actual_data = [1, 2, 3]
        baseline_data = [4, 5, 6]
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        
        assert resolve(ctx.actual) == actual_data
        assert ctx.baseline == baseline_data

    def test_init_with_none_baseline(self):
        """Test initialization with None baseline."""
        actual = SafeObject({"key": "value"})
        
        ctx = CheckContext(actual=actual, baseline=None)
        
        assert ctx.baseline is None
        assert ctx.root_baseline is None


class TestCheckContextChild:
    """Test CheckContext child method."""

    def test_child_with_dict_key(self):
        """Test creating a child context with a dictionary key."""
        actual_data = {"name": "John", "age": 30}
        baseline_data = {"name": "Jane", "age": 25}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        child_ctx = ctx.child("name")
        
        assert resolve(child_ctx.actual) == "John"
        assert child_ctx.baseline == "Jane"
        assert child_ctx.path == ["name"]
        assert child_ctx.root_actual is actual
        assert child_ctx.root_baseline is baseline_data

    def test_child_with_list_index(self):
        """Test creating a child context with a list index."""
        actual_data = [10, 20, 30]
        baseline_data = [100, 200, 300]
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        child_ctx = ctx.child(1)
        
        assert resolve(child_ctx.actual) == 20
        assert child_ctx.baseline == 200
        assert child_ctx.path == [1]

    def test_nested_child_contexts(self):
        """Test creating nested child contexts."""
        actual_data = {"user": {"profile": {"name": "John"}}}
        baseline_data = {"user": {"profile": {"name": "Jane"}}}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        child1 = ctx.child("user")
        child2 = child1.child("profile")
        child3 = child2.child("name")
        
        assert resolve(child3.actual) == "John"
        assert child3.baseline == "Jane"
        assert child3.path == ["user", "profile", "name"]
        assert child3.root_actual is actual
        assert child3.root_baseline is baseline_data

    def test_child_preserves_root_references(self):
        """Test that child contexts preserve root references."""
        actual_data = {"a": {"b": {"c": "value"}}}
        baseline_data = {"a": {"b": {"c": "other"}}}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        
        # Create multiple levels of children
        child = ctx.child("a").child("b").child("c")
        
        # Root references should be preserved
        assert child.root_actual is actual
        assert child.root_baseline is baseline_data

    def test_child_path_accumulation(self):
        """Test that path accumulates correctly through child contexts."""
        actual_data = {"level1": {"level2": {"level3": "value"}}}
        baseline_data = {"level1": {"level2": {"level3": "other"}}}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        
        # Verify path at each level
        child1 = ctx.child("level1")
        assert child1.path == ["level1"]
        
        child2 = child1.child("level2")
        assert child2.path == ["level1", "level2"]
        
        child3 = child2.child("level3")
        assert child3.path == ["level1", "level2", "level3"]

    def test_child_does_not_modify_parent_path(self):
        """Test that creating a child does not modify the parent's path."""
        actual_data = {"a": {"b": "value"}}
        baseline_data = {"a": {"b": "other"}}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        original_path = ctx.path.copy()
        
        _ = ctx.child("a")
        
        assert ctx.path == original_path

    def test_multiple_children_from_same_parent(self):
        """Test creating multiple children from the same parent context."""
        actual_data = {"name": "John", "age": 30, "city": "NYC"}
        baseline_data = {"name": "Jane", "age": 25, "city": "LA"}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        
        child_name = ctx.child("name")
        child_age = ctx.child("age")
        child_city = ctx.child("city")
        
        assert child_name.path == ["name"]
        assert child_age.path == ["age"]
        assert child_city.path == ["city"]
        
        assert resolve(child_name.actual) == "John"
        assert resolve(child_age.actual) == 30
        assert resolve(child_city.actual) == "NYC"


class TestCheckContextWithMixedTypes:
    """Test CheckContext with mixed data types."""

    def test_dict_containing_list(self):
        """Test context with dictionary containing lists."""
        actual_data = {"items": [1, 2, 3]}
        baseline_data = {"items": [4, 5, 6]}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        items_ctx = ctx.child("items")
        item_ctx = items_ctx.child(0)
        
        assert resolve(item_ctx.actual) == 1
        assert item_ctx.baseline == 4
        assert item_ctx.path == ["items", 0]

    def test_list_containing_dicts(self):
        """Test context with list containing dictionaries."""
        actual_data = [{"name": "John"}, {"name": "Jane"}]
        baseline_data = [{"name": "Alice"}, {"name": "Bob"}]
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        first_item = ctx.child(0)
        name_ctx = first_item.child("name")
        
        assert resolve(name_ctx.actual) == "John"
        assert name_ctx.baseline == "Alice"
        assert name_ctx.path == [0, "name"]


class TestCheckContextEdgeCases:
    """Test edge cases for CheckContext."""

    def test_empty_dict(self):
        """Test context with empty dictionaries."""
        actual = SafeObject({})
        baseline = {}
        
        ctx = CheckContext(actual=actual, baseline=baseline)
        
        assert resolve(ctx.actual) == {}
        assert ctx.baseline == {}

    def test_empty_list(self):
        """Test context with empty lists."""
        actual = SafeObject([])
        baseline = []
        
        ctx = CheckContext(actual=actual, baseline=baseline)
        
        assert resolve(ctx.actual) == []
        assert ctx.baseline == []

    def test_path_with_integer_and_string_keys(self):
        """Test path with mixed integer and string keys."""
        actual_data = {"users": [{"name": "John"}]}
        baseline_data = {"users": [{"name": "Jane"}]}
        actual = SafeObject(actual_data)
        
        ctx = CheckContext(actual=actual, baseline=baseline_data)
        child = ctx.child("users").child(0).child("name")
        
        assert child.path == ["users", 0, "name"]