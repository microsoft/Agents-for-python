# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the Unset singleton class."""

import pytest

from microsoft_agents.testing.core.fluent.backend.types.unset import Unset


class TestUnset:
    """Tests for the Unset singleton."""

    def test_unset_is_singleton_instance(self):
        """Unset should be a singleton instance, not a class."""
        # Unset is reassigned to an instance at the end of the module
        assert not isinstance(Unset, type)
        assert isinstance(Unset, object)

    def test_unset_bool_is_false(self):
        """Unset should evaluate to False in boolean context."""
        assert bool(Unset) is False
        assert not Unset

    def test_unset_repr(self):
        """Unset should have 'Unset' as its repr."""
        assert repr(Unset) == "Unset"

    def test_unset_str(self):
        """Unset should have 'Unset' as its string representation."""
        assert str(Unset) == "Unset"

    def test_unset_get_returns_self(self):
        """Calling get() on Unset should return Unset itself."""
        result = Unset.get()
        assert result is Unset

    def test_unset_get_with_args_returns_self(self):
        """Calling get() with arguments should still return Unset."""
        result = Unset.get("default", key="value")
        assert result is Unset

    def test_unset_getattr_returns_self(self):
        """Accessing any attribute on Unset should return Unset."""
        assert Unset.any_attribute is Unset
        assert Unset.nested.deep.attribute is Unset
        assert Unset.foo.bar.baz is Unset

    def test_unset_getitem_returns_self(self):
        """Accessing any item on Unset should return Unset."""
        assert Unset["key"] is Unset
        assert Unset[0] is Unset
        assert Unset["nested"]["key"] is Unset

    def test_unset_setattr_raises(self):
        """Setting an attribute on Unset should raise AttributeError (readonly)."""
        with pytest.raises(AttributeError):
            Unset.new_attr = "value"

    def test_unset_delattr_raises(self):
        """Deleting an attribute on Unset should raise AttributeError (readonly)."""
        with pytest.raises(AttributeError):
            del Unset.some_attr

    def test_unset_setitem_raises(self):
        """Setting an item on Unset should raise AttributeError (readonly)."""
        with pytest.raises(AttributeError):
            Unset["key"] = "value"

    def test_unset_delitem_raises(self):
        """Deleting an item on Unset should raise AttributeError (readonly)."""
        with pytest.raises(AttributeError):
            del Unset["key"]

    def test_unset_in_if_statement(self):
        """Unset should work correctly in if statements."""
        if Unset:
            result = "truthy"
        else:
            result = "falsy"
        
        assert result == "falsy"

    def test_unset_identity(self):
        """Chained access should return the same Unset instance."""
        result = Unset.a.b.c["d"]["e"].f
        assert result is Unset

    def test_unset_can_be_compared(self):
        """Unset should be comparable using identity."""
        value = Unset.some_missing_key
        assert value is Unset

    def test_unset_in_conditional_expression(self):
        """Unset should work in conditional expressions."""
        value = Unset
        result = "found" if value else "not found"
        assert result == "not found"

    def test_unset_or_default(self):
        """Unset should work with 'or' for default values."""
        value = Unset or "default"
        assert value == "default"

    def test_unset_and_short_circuit(self):
        """Unset should short-circuit 'and' expressions."""
        value = Unset and "never reached"
        assert value is Unset
