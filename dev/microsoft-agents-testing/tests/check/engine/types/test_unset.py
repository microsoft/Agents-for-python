"""
Unit tests for the Unset singleton class.

This module tests:
- Unset singleton behavior
- get() method returning self
- __getattr__ returning self
- __getitem__ returning self
- __bool__ returning False
- __repr__ and __str__
"""

import pytest
from microsoft_agents.testing.check.engine.types.unset import Unset


# =============================================================================
# Singleton Behavior Tests
# =============================================================================

class TestUnsetSingleton:
    """Test Unset singleton behavior."""
    
    def test_unset_is_falsy(self):
        assert bool(Unset) is False
    
    def test_unset_is_singleton(self):
        # Unset should be the same instance
        assert Unset is Unset


# =============================================================================
# get() Method Tests
# =============================================================================

class TestUnsetGet:
    """Test the get() method."""
    
    def test_get_returns_self(self):
        result = Unset.get()
        assert result is Unset
    
    def test_get_with_args_returns_self(self):
        result = Unset.get("some", "args")
        assert result is Unset
    
    def test_get_with_kwargs_returns_self(self):
        result = Unset.get(key="value")
        assert result is Unset


# =============================================================================
# __getattr__ Tests
# =============================================================================

class TestUnsetGetAttr:
    """Test __getattr__ behavior."""
    
    def test_getattr_returns_self(self):
        result = Unset.some_attribute
        assert result is Unset
    
    def test_getattr_chained_returns_self(self):
        result = Unset.some.deeply.nested.attribute
        assert result is Unset
    
    def test_getattr_any_name(self):
        assert Unset.foo is Unset
        assert Unset.bar is Unset
        assert Unset._private is Unset


# =============================================================================
# __getitem__ Tests
# =============================================================================

class TestUnsetGetItem:
    """Test __getitem__ behavior."""
    
    def test_getitem_returns_self(self):
        result = Unset["key"]
        assert result is Unset
    
    def test_getitem_with_int_index(self):
        result = Unset[0]
        assert result is Unset
    
    def test_getitem_chained_returns_self(self):
        result = Unset["a"]["b"]["c"]
        assert result is Unset


# =============================================================================
# Boolean Behavior Tests
# =============================================================================

class TestUnsetBoolean:
    """Test boolean conversion."""
    
    def test_bool_is_false(self):
        assert bool(Unset) is False
    
    def test_if_condition(self):
        if Unset:
            pytest.fail("Unset should be falsy")
    
    def test_not_unset(self):
        assert not Unset


# =============================================================================
# String Representation Tests
# =============================================================================

class TestUnsetStringRepresentation:
    """Test string representations."""
    
    def test_repr(self):
        assert repr(Unset) == "Unset"
    
    def test_str(self):
        assert str(Unset) == "Unset"


# =============================================================================
# Readonly Behavior Tests
# =============================================================================

class TestUnsetReadonly:
    """Test that Unset inherits Readonly behavior."""
    
    def test_setattr_raises(self):
        with pytest.raises(AttributeError):
            Unset.new_attr = "value"
    
    def test_delattr_raises(self):
        with pytest.raises(AttributeError):
            del Unset.some_attr
    
    def test_setitem_raises(self):
        with pytest.raises(AttributeError):
            Unset["key"] = "value"
    
    def test_delitem_raises(self):
        with pytest.raises(AttributeError):
            del Unset["key"]


# =============================================================================
# Integration Tests
# =============================================================================

class TestUnsetIntegration:
    """Integration tests for Unset."""
    
    def test_can_check_for_unset(self):
        value = Unset
        is_unset = value is Unset
        assert is_unset is True
    
    def test_unset_in_conditional(self):
        value = Unset
        
        # Common pattern to check for unset values
        if value is Unset:
            result = "default"
        else:
            result = value
        
        assert result == "default"
    
    def test_chained_access_pattern(self):
        # Simulating safe access pattern
        data = Unset
        
        # Should be able to chain without errors
        result = data.user.profile.name
        assert result is Unset
        assert bool(result) is False
