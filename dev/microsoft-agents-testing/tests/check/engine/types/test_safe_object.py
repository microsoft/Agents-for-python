"""
Unit tests for the SafeObject class and helper functions.

This module tests:
- SafeObject initialization
- resolve() function
- parent() function
- __getattr__ safe attribute access
- __getitem__ safe item access
- __eq__ equality comparison
- __str__ and __repr__
"""

import pytest
from microsoft_agents.testing.check.engine.types.safe_object import SafeObject, resolve, parent
from microsoft_agents.testing.check.engine.types.unset import Unset


# =============================================================================
# SafeObject Initialization Tests
# =============================================================================

class TestSafeObjectInit:
    """Test SafeObject initialization."""
    
    def test_init_with_dict(self):
        obj = SafeObject({"key": "value"})
        assert resolve(obj) == {"key": "value"}
    
    def test_init_with_list(self):
        obj = SafeObject([1, 2, 3])
        assert resolve(obj) == [1, 2, 3]
    
    def test_init_with_string(self):
        obj = SafeObject("hello")
        assert resolve(obj) == "hello"
    
    def test_init_with_int(self):
        obj = SafeObject(42)
        assert resolve(obj) == 42
    
    def test_init_with_none(self):
        obj = SafeObject(None)
        assert resolve(obj) is None
    
    def test_init_with_parent(self):
        parent_obj = SafeObject({"nested": {"value": 1}})
        child_obj = SafeObject({"value": 1}, parent_obj)
        
        assert parent(child_obj) == parent_obj
    
    def test_init_without_parent(self):
        obj = SafeObject({"key": "value"})
        assert parent(obj) is None
    
    def test_init_with_safe_object_returns_same(self):
        original = SafeObject({"test": True})
        wrapped = SafeObject(original)
        
        assert wrapped is original


# =============================================================================
# resolve() Function Tests
# =============================================================================

class TestResolveFunction:
    """Test the resolve() function."""
    
    def test_resolve_safe_object(self):
        obj = SafeObject({"data": "test"})
        assert resolve(obj) == {"data": "test"}
    
    def test_resolve_non_safe_object(self):
        plain_dict = {"data": "test"}
        assert resolve(plain_dict) == {"data": "test"}
    
    def test_resolve_primitive(self):
        assert resolve(42) == 42
        assert resolve("string") == "string"
        assert resolve(True) is True
    
    def test_resolve_nested_safe_object(self):
        inner = {"nested": "value"}
        outer = SafeObject(inner)
        assert resolve(outer) == inner


# =============================================================================
# parent() Function Tests
# =============================================================================

class TestParentFunction:
    """Test the parent() function."""
    
    def test_parent_returns_parent_object(self):
        parent_obj = SafeObject({"parent": True})
        child_value = {"child": True}
        child_obj = SafeObject(child_value, parent_obj)
        
        assert parent(child_obj) == parent_obj
    
    def test_parent_returns_none_when_no_parent(self):
        obj = SafeObject({"solo": True})
        assert parent(obj) is None


# =============================================================================
# __getattr__ Tests
# =============================================================================

class TestSafeObjectGetAttr:
    """Test safe attribute access."""
    
    def test_getattr_existing_dict_key(self):
        obj = SafeObject({"name": "Alice", "age": 30})
        name_obj = obj.name
        
        assert resolve(name_obj) == "Alice"
    
    def test_getattr_missing_key_returns_unset(self):
        obj = SafeObject({"name": "Alice"})
        missing = obj.nonexistent
        
        assert resolve(missing) is Unset
    
    def test_getattr_nested_access(self):
        obj = SafeObject({"user": {"profile": {"name": "Bob"}}})
        name = obj.user.profile.name
        
        assert resolve(name) == "Bob"
    
    def test_getattr_chain_to_missing(self):
        obj = SafeObject({"user": {"name": "Alice"}})
        # Accessing non-existent nested path should return Unset
        result = obj.user.profile.missing
        
        assert resolve(result) is Unset


# =============================================================================
# __getitem__ Tests
# =============================================================================

class TestSafeObjectGetItem:
    """Test safe item access."""
    
    def test_getitem_dict_key(self):
        obj = SafeObject({"key": "value"})
        item = obj["key"]
        
        assert resolve(item) == "value"
    
    def test_getitem_list_index(self):
        obj = SafeObject([10, 20, 30])
        item = obj[1]
        
        assert resolve(item) == 20
    
    def test_getitem_missing_key_returns_unset(self):
        obj = SafeObject({"key": "value"})
        missing = obj["nonexistent"]
        
        assert resolve(missing) is Unset
    
    def test_getitem_nested(self):
        obj = SafeObject({"items": [{"id": 1}, {"id": 2}]})
        item_id = obj["items"][0]["id"]
        
        assert resolve(item_id) == 1


# =============================================================================
# __str__ and __repr__ Tests
# =============================================================================

class TestSafeObjectStringRepresentation:
    """Test string representations."""
    
    def test_str_returns_value_string(self):
        obj = SafeObject("hello")
        assert str(obj) == "hello"
    
    def test_str_dict(self):
        obj = SafeObject({"key": "value"})
        assert "key" in str(obj)
        assert "value" in str(obj)
    
    def test_str_int(self):
        obj = SafeObject(42)
        assert str(obj) == "42"


# =============================================================================
# Readonly Behavior Tests
# =============================================================================

class TestSafeObjectReadonly:
    """Test that SafeObject inherits Readonly behavior."""
    
    def test_setattr_raises(self):
        obj = SafeObject({"value": 1})
        with pytest.raises(AttributeError):
            obj.new_attr = "test"
    
    def test_delattr_raises(self):
        obj = SafeObject({"value": 1})
        with pytest.raises(AttributeError):
            del obj.value
    
    def test_setitem_raises(self):
        obj = SafeObject({"value": 1})
        with pytest.raises(AttributeError):
            obj["value"] = 2
    
    def test_delitem_raises(self):
        obj = SafeObject({"value": 1})
        with pytest.raises(AttributeError):
            del obj["value"]


# =============================================================================
# Integration Tests
# =============================================================================

class TestSafeObjectIntegration:
    """Integration tests for SafeObject."""
    
    def test_complex_nested_access(self):
        data = {
            "users": [
                {"name": "Alice", "scores": [85, 90]},
                {"name": "Bob", "scores": [78, 82]},
            ],
            "meta": {"count": 2}
        }
        obj = SafeObject(data)
        
        # Access nested values
        assert resolve(obj.users[0].name) == "Alice"
        assert resolve(obj.users[1].scores[1]) == 82
        assert resolve(obj.meta.count) == 2
    
    def test_safe_access_to_missing_nested(self):
        data = {"user": {"name": "Alice"}}
        obj = SafeObject(data)
        
        # Deep access to missing values should return Unset
        result = obj.user.profile.address.city
        assert resolve(result) is Unset
    
    def test_parent_chain(self):
        data = {"level1": {"level2": {"level3": "deep"}}}
        obj = SafeObject(data)
        
        level1 = obj["level1"]
        level2 = level1["level2"]
        
        # Check parent relationships
        assert parent(level2) == level1
        assert parent(level1) == obj
