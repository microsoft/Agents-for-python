"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest
from microsoft.agents.builder.app.state.memory import Memory
from microsoft.agents.builder.app import ApplicationError


class TestMemory:
    """Tests for the Memory class."""

    def test_memory_initialization(self):
        """Test that Memory initializes properly."""
        memory = Memory()
        assert memory._parent is None
        assert memory._scopes == {}

    def test_memory_with_parent(self):
        """Test that Memory with parent initializes properly."""
        parent = Memory()
        child = Memory(parent)
        assert child._parent == parent
        assert child._scopes == {}

    def test_set_and_get_value(self):
        """Test setting and getting a value."""
        memory = Memory()
        memory.set("test.value", 42)
        assert memory.get("test.value") == 42

    def test_get_non_existent_value(self):
        """Test getting a non-existent value returns None."""
        memory = Memory()
        assert memory.get("test.non_existent") is None

    def test_set_and_get_without_scope(self):
        """Test setting and getting a value without specifying a scope."""
        memory = Memory()
        memory.set("value", 42)  # No scope specified, should use 'temp'
        assert memory.get("value") == 42
        assert memory.get("temp.value") == 42  # Equivalent to above

    def test_has_value(self):
        """Test checking if a value exists."""
        memory = Memory()
        memory.set("test.value", 42)
        assert memory.has("test.value") is True
        assert memory.has("nonexistent.value") is False

    def test_has_value_without_scope(self):
        """Test checking if a value exists without specifying a scope."""
        memory = Memory()
        memory.set("value", 42)  # No scope specified, should use 'temp'
        assert memory.has("value") is True
        assert memory.has("temp.value") is True  # Equivalent to above

    def test_delete_value(self):
        """Test deleting a value."""
        memory = Memory()
        memory.set("test.value", 42)
        assert memory.has("test.value") is True
        memory.delete("test.value")
        assert memory.has("test.value") is False
        assert memory.get("test.value") is None

    def test_delete_value_without_scope(self):
        """Test deleting a value without specifying a scope."""
        memory = Memory()
        memory.set("value", 42)  # No scope specified, should use 'temp'
        assert memory.has("value") is True
        memory.delete("value")
        assert memory.has("value") is False
        assert memory.get("value") is None

    def test_scopes_isolation(self):
        """Test that different scopes are isolated."""
        memory = Memory()
        memory.set("scope1.value", 42)
        memory.set("scope2.value", 84)
        assert memory.get("scope1.value") == 42
        assert memory.get("scope2.value") == 84

    def test_invalid_path_raises_error(self):
        """Test that an invalid path raises an ApplicationError."""
        memory = Memory()
        with pytest.raises(ApplicationError):
            memory.set("too.many.parts", 42)
        with pytest.raises(ApplicationError):
            memory.get("too.many.parts")
        with pytest.raises(ApplicationError):
            memory.has("too.many.parts")
        with pytest.raises(ApplicationError):
            memory.delete("too.many.parts")

    def test_memory_hierarchy(self):
        """Test that memory hierarchy works correctly."""
        parent = Memory()
        child = Memory(parent)

        parent.set("test.parent_value", "parent")
        child.set("test.child_value", "child")

        # Child should be able to access parent's values
        assert child.has("test.parent_value") is True
        assert child.get("test.parent_value") == "parent"

        # Parent should not be able to access child's values
        assert parent.has("test.child_value") is False
        assert parent.get("test.child_value") is None

        # Child values override parent values
        parent.set("test.common", "parent_value")
        child.set("test.common", "child_value")
        assert child.get("test.common") == "child_value"
        assert parent.get("test.common") == "parent_value"

    def test_shadow_parent_value(self):
        """Test that child values shadow parent values."""
        parent = Memory()
        child = Memory(parent)

        parent.set("test.value", "parent_value")
        assert child.get("test.value") == "parent_value"

        # Shadow the parent value
        child.set("test.value", "child_value")
        assert child.get("test.value") == "child_value"
        assert parent.get("test.value") == "parent_value"

        # Delete the child value, should reveal the parent value again
        child.delete("test.value")
        assert child.get("test.value") == "parent_value"
