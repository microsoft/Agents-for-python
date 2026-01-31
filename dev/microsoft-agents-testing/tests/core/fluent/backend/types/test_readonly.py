# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the Readonly mixin class."""

import pytest

from microsoft_agents.testing.core.fluent.backend.types.readonly import Readonly


class ReadonlySubclass(Readonly):
    """A test subclass that uses the Readonly mixin."""
    
    def __init__(self):
        # Use object.__setattr__ to bypass the readonly protection during init
        object.__setattr__(self, "initial_value", 42)
        object.__setattr__(self, "_data", {"key": "value"})


class TestReadonly:
    """Tests for the Readonly mixin class."""

    def test_setattr_raises_attribute_error(self):
        """Setting an attribute should raise AttributeError."""
        obj = ReadonlySubclass()
        
        with pytest.raises(AttributeError) as exc_info:
            obj.new_attribute = "value"
        
        assert "Cannot set attribute 'new_attribute'" in str(exc_info.value)
        assert "ReadonlySubclass" in str(exc_info.value)

    def test_setattr_raises_for_existing_attribute(self):
        """Setting an existing attribute should also raise AttributeError."""
        obj = ReadonlySubclass()
        
        with pytest.raises(AttributeError) as exc_info:
            obj.initial_value = 100
        
        assert "Cannot set attribute 'initial_value'" in str(exc_info.value)

    def test_delattr_raises_attribute_error(self):
        """Deleting an attribute should raise AttributeError."""
        obj = ReadonlySubclass()
        
        with pytest.raises(AttributeError) as exc_info:
            del obj.initial_value
        
        assert "Cannot delete attribute 'initial_value'" in str(exc_info.value)
        assert "ReadonlySubclass" in str(exc_info.value)

    def test_delattr_raises_for_nonexistent_attribute(self):
        """Deleting a non-existent attribute should also raise AttributeError."""
        obj = ReadonlySubclass()
        
        with pytest.raises(AttributeError) as exc_info:
            del obj.nonexistent
        
        assert "Cannot delete attribute 'nonexistent'" in str(exc_info.value)

    def test_setitem_raises_attribute_error(self):
        """Setting an item should raise AttributeError."""
        obj = ReadonlySubclass()
        
        with pytest.raises(AttributeError) as exc_info:
            obj["key"] = "new_value"
        
        assert "Cannot set item 'key'" in str(exc_info.value)
        assert "ReadonlySubclass" in str(exc_info.value)

    def test_delitem_raises_attribute_error(self):
        """Deleting an item should raise AttributeError."""
        obj = ReadonlySubclass()
        
        with pytest.raises(AttributeError) as exc_info:
            del obj["key"]
        
        assert "Cannot delete item 'key'" in str(exc_info.value)
        assert "ReadonlySubclass" in str(exc_info.value)

    def test_getattr_still_works(self):
        """Getting attributes should still work normally."""
        obj = ReadonlySubclass()
        
        assert obj.initial_value == 42

    def test_object_setattr_bypasses_protection(self):
        """Using object.__setattr__ should bypass the protection."""
        obj = ReadonlySubclass()
        
        # This is the escape hatch for initialization
        object.__setattr__(obj, "new_attr", "bypassed")
        
        assert obj.new_attr == "bypassed"

    def test_multiple_readonly_instances_are_independent(self):
        """Multiple Readonly instances should be independent."""
        obj1 = ReadonlySubclass()
        obj2 = ReadonlySubclass()
        
        # Modify obj1 via escape hatch
        object.__setattr__(obj1, "initial_value", 100)
        
        # obj2 should be unaffected
        assert obj1.initial_value == 100
        assert obj2.initial_value == 42
