"""
Unit tests for the Readonly mixin class.

This module tests:
- __setattr__ prevention
- __delattr__ prevention
- __setitem__ prevention
- __delitem__ prevention
"""

import pytest
from microsoft_agents.testing.check.engine.types.readonly import Readonly


# =============================================================================
# Test Class Using Readonly Mixin
# =============================================================================

class ReadonlyTestClass(Readonly):
    """A test class that uses the Readonly mixin."""
    
    def __init__(self, value):
        # Use object.__setattr__ to bypass Readonly for initialization
        object.__setattr__(self, 'value', value)


class ReadonlyDictLike(Readonly):
    """A test class that mimics dict-like behavior with Readonly."""
    
    def __init__(self, data):
        object.__setattr__(self, '_data', data)
    
    def __getitem__(self, key):
        return self._data[key]


# =============================================================================
# __setattr__ Prevention Tests
# =============================================================================

class TestReadonlySetAttr:
    """Test __setattr__ prevention."""
    
    def test_setattr_raises_attribute_error(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError) as exc_info:
            obj.value = 100
        
        assert "Cannot set attribute 'value'" in str(exc_info.value)
    
    def test_setattr_new_attribute_raises(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError) as exc_info:
            obj.new_attr = "test"
        
        assert "Cannot set attribute 'new_attr'" in str(exc_info.value)
    
    def test_setattr_error_includes_class_name(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError) as exc_info:
            obj.test = "value"
        
        assert "ReadonlyTestClass" in str(exc_info.value)


# =============================================================================
# __delattr__ Prevention Tests
# =============================================================================

class TestReadonlyDelAttr:
    """Test __delattr__ prevention."""
    
    def test_delattr_raises_attribute_error(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError) as exc_info:
            del obj.value
        
        assert "Cannot delete attribute 'value'" in str(exc_info.value)
    
    def test_delattr_nonexistent_raises(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError) as exc_info:
            del obj.nonexistent
        
        assert "Cannot delete attribute 'nonexistent'" in str(exc_info.value)
    
    def test_delattr_error_includes_class_name(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError) as exc_info:
            del obj.test
        
        assert "ReadonlyTestClass" in str(exc_info.value)


# =============================================================================
# __setitem__ Prevention Tests
# =============================================================================

class TestReadonlySetItem:
    """Test __setitem__ prevention."""
    
    def test_setitem_raises_attribute_error(self):
        obj = ReadonlyDictLike({"key": "value"})
        
        with pytest.raises(AttributeError) as exc_info:
            obj["key"] = "new_value"
        
        assert "Cannot set item 'key'" in str(exc_info.value)
    
    def test_setitem_new_key_raises(self):
        obj = ReadonlyDictLike({})
        
        with pytest.raises(AttributeError) as exc_info:
            obj["new_key"] = "value"
        
        assert "Cannot set item 'new_key'" in str(exc_info.value)
    
    def test_setitem_error_includes_class_name(self):
        obj = ReadonlyDictLike({})
        
        with pytest.raises(AttributeError) as exc_info:
            obj["test"] = "value"
        
        assert "ReadonlyDictLike" in str(exc_info.value)


# =============================================================================
# __delitem__ Prevention Tests
# =============================================================================

class TestReadonlyDelItem:
    """Test __delitem__ prevention."""
    
    def test_delitem_raises_attribute_error(self):
        obj = ReadonlyDictLike({"key": "value"})
        
        with pytest.raises(AttributeError) as exc_info:
            del obj["key"]
        
        assert "Cannot delete item 'key'" in str(exc_info.value)
    
    def test_delitem_nonexistent_key_raises(self):
        obj = ReadonlyDictLike({})
        
        with pytest.raises(AttributeError) as exc_info:
            del obj["nonexistent"]
        
        assert "Cannot delete item 'nonexistent'" in str(exc_info.value)
    
    def test_delitem_error_includes_class_name(self):
        obj = ReadonlyDictLike({})
        
        with pytest.raises(AttributeError) as exc_info:
            del obj["test"]
        
        assert "ReadonlyDictLike" in str(exc_info.value)


# =============================================================================
# Read Access Tests
# =============================================================================

class TestReadonlyReadAccess:
    """Test that read access still works."""
    
    def test_getattr_works(self):
        obj = ReadonlyTestClass(42)
        assert obj.value == 42
    
    def test_getitem_works(self):
        obj = ReadonlyDictLike({"key": "value"})
        assert obj["key"] == "value"


# =============================================================================
# Inheritance Tests
# =============================================================================

class TestReadonlyInheritance:
    """Test Readonly behavior in inheritance."""
    
    def test_subclass_inherits_readonly(self):
        class SubReadonly(ReadonlyTestClass):
            pass
        
        obj = SubReadonly(42)
        
        with pytest.raises(AttributeError):
            obj.value = 100
        
        with pytest.raises(AttributeError):
            obj.new = "value"
    
    def test_multiple_inheritance(self):
        class Base:
            pass
        
        class Combined(Base, Readonly):
            def __init__(self):
                object.__setattr__(self, 'data', 42)
        
        obj = Combined()
        
        with pytest.raises(AttributeError):
            obj.data = 100


# =============================================================================
# Edge Cases
# =============================================================================

class TestReadonlyEdgeCases:
    """Test edge cases for Readonly mixin."""
    
    def test_special_attribute_names(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError):
            obj.__custom__ = "value"
    
    def test_private_attribute_names(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError):
            obj._private = "value"
    
    def test_dunder_attribute_names(self):
        obj = ReadonlyTestClass(42)
        
        with pytest.raises(AttributeError):
            obj.__test = "value"
