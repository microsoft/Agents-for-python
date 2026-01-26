# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from microsoft_agents.testing.utils.data_utils import (
    expand,
    _merge,
    _resolve_kwargs,
    deep_update,
    set_defaults,
)


class TestExpand:
    """Test the expand function."""

    def test_expand_flat_dict(self):
        """Test that a flat dict without dots stays the same."""
        data = {"a": 1, "b": 2}
        result = expand(data)
        assert result == {"a": 1, "b": 2}

    def test_expand_single_level_nested(self):
        """Test expanding a single level of nesting."""
        data = {"a.b": 1}
        result = expand(data)
        assert result == {"a": {"b": 1}}

    def test_expand_multiple_levels_nested(self):
        """Test expanding multiple levels of nesting."""
        data = {"a.b.c": 1}
        result = expand(data)
        assert result == {"a": {"b": {"c": 1}}}

    def test_expand_mixed_flat_and_nested(self):
        """Test expanding a dict with both flat and nested keys."""
        data = {"a": 1, "b.c": 2}
        result = expand(data)
        assert result == {"a": 1, "b": {"c": 2}}

    def test_expand_multiple_keys_same_root(self):
        """Test expanding multiple keys with the same root."""
        data = {"a.b": 1, "a.c": 2}
        result = expand(data)
        assert result == {"a": {"b": 1, "c": 2}}

    def test_expand_non_dict_returns_as_is(self):
        """Test that non-dict values are returned unchanged."""
        assert expand("string") == "string"
        assert expand(123) == 123
        assert expand([1, 2, 3]) == [1, 2, 3]
        assert expand(None) is None

    def test_expand_empty_dict(self):
        """Test expanding an empty dict."""
        result = expand({})
        assert result == {}

    def test_expand_custom_level_separator(self):
        """Test expanding with a custom level separator."""
        data = {"a/b/c": 1}
        result = expand(data, level_sep="/")
        assert result == {"a": {"b": {"c": 1}}}

    def test_expand_conflicting_keys_raises_error(self):
        """Test that conflicting keys raise a RuntimeError."""
        # Same root with both flat and nested keys
        data = {"a": 1, "a.b": 2}
        with pytest.raises(RuntimeError):
            expand(data)

    def test_expand_duplicate_nested_path_raises_error(self):
        """Test that duplicate nested paths raise a RuntimeError."""
        data = {"a.b": 1}
        # Simulate adding a duplicate by pre-populating new_data
        # This is tested indirectly - in practice this would need a dict
        # where the same path appears twice, which Python dicts don't allow

    def test_expand_deeply_nested(self):
        """Test expanding a deeply nested structure."""
        data = {"a.b.c.d.e": "deep"}
        result = expand(data)
        assert result == {"a": {"b": {"c": {"d": {"e": "deep"}}}}}

    def test_expand_preserves_complex_values(self):
        """Test that complex values (lists, dicts) are preserved."""
        data = {"a.b": [1, 2, 3], "c.d": {"nested": "dict"}}
        result = expand(data)
        assert result == {"a": {"b": [1, 2, 3]}, "c": {"d": {"nested": "dict"}}}


class TestMerge:
    """Test the _merge function."""

    def test_merge_empty_dicts(self):
        """Test merging two empty dicts."""
        original = {}
        other = {}
        _merge(original, other)
        assert original == {}

    def test_merge_into_empty_dict(self):
        """Test merging into an empty dict."""
        original = {}
        other = {"a": 1, "b": 2}
        _merge(original, other)
        assert original == {"a": 1, "b": 2}

    def test_merge_from_empty_dict(self):
        """Test merging from an empty dict."""
        original = {"a": 1, "b": 2}
        other = {}
        _merge(original, other)
        assert original == {"a": 1, "b": 2}

    def test_merge_non_overlapping_keys(self):
        """Test merging dicts with non-overlapping keys."""
        original = {"a": 1}
        other = {"b": 2}
        _merge(original, other)
        assert original == {"a": 1, "b": 2}

    def test_merge_overlapping_keys_overwrite_true(self):
        """Test that overlapping keys are overwritten when overwrite_leaves=True."""
        original = {"a": 1}
        other = {"a": 2}
        _merge(original, other, overwrite_leaves=True)
        assert original == {"a": 2}

    def test_merge_overlapping_keys_overwrite_false(self):
        """Test that overlapping keys are preserved when overwrite_leaves=False."""
        original = {"a": 1}
        other = {"a": 2}
        _merge(original, other, overwrite_leaves=False)
        assert original == {"a": 1}

    def test_merge_nested_dicts(self):
        """Test merging nested dicts."""
        original = {"a": {"b": 1}}
        other = {"a": {"c": 2}}
        _merge(original, other)
        assert original == {"a": {"b": 1, "c": 2}}

    def test_merge_nested_dicts_overwrite_leaves(self):
        """Test merging nested dicts with overlapping leaves."""
        original = {"a": {"b": 1}}
        other = {"a": {"b": 2}}
        _merge(original, other, overwrite_leaves=True)
        assert original == {"a": {"b": 2}}

    def test_merge_nested_dicts_no_overwrite_leaves(self):
        """Test merging nested dicts without overwriting leaves."""
        original = {"a": {"b": 1}}
        other = {"a": {"b": 2}}
        _merge(original, other, overwrite_leaves=False)
        assert original == {"a": {"b": 1}}

    def test_merge_deeply_nested(self):
        """Test merging deeply nested structures."""
        original = {"a": {"b": {"c": 1}}}
        other = {"a": {"b": {"d": 2}}}
        _merge(original, other)
        assert original == {"a": {"b": {"c": 1, "d": 2}}}


class TestResolveKwargs:
    """Test the _resolve_kwargs function."""

    def test_resolve_kwargs_empty(self):
        """Test with no arguments."""
        result = _resolve_kwargs()
        assert result == {}

    def test_resolve_kwargs_only_data(self):
        """Test with only data argument."""
        result = _resolve_kwargs({"a": 1})
        assert result == {"a": 1}

    def test_resolve_kwargs_only_kwargs(self):
        """Test with only keyword arguments."""
        result = _resolve_kwargs(a=1, b=2)
        assert result == {"a": 1, "b": 2}

    def test_resolve_kwargs_data_and_kwargs(self):
        """Test with both data and keyword arguments."""
        result = _resolve_kwargs({"a": 1}, b=2)
        assert result == {"a": 1, "b": 2}

    def test_resolve_kwargs_kwargs_override_data(self):
        """Test that kwargs override data values."""
        result = _resolve_kwargs({"a": 1}, a=2)
        assert result == {"a": 2}

    def test_resolve_kwargs_deep_copy(self):
        """Test that the original data is not modified."""
        original = {"a": {"b": 1}}
        result = _resolve_kwargs(original, c=2)
        assert result == {"a": {"b": 1}, "c": 2}
        assert original == {"a": {"b": 1}}  # Original unchanged

    def test_resolve_kwargs_none_data(self):
        """Test with None as data."""
        result = _resolve_kwargs(None, a=1)
        assert result == {"a": 1}


class TestDeepUpdate:
    """Test the deep_update function."""

    def test_deep_update_empty(self):
        """Test updating with empty updates."""
        original = {"a": 1}
        deep_update(original)
        assert original == {"a": 1}

    def test_deep_update_with_dict(self):
        """Test updating with a dict."""
        original = {"a": 1}
        deep_update(original, {"b": 2})
        assert original == {"a": 1, "b": 2}

    def test_deep_update_with_kwargs(self):
        """Test updating with kwargs."""
        original = {"a": 1}
        deep_update(original, b=2)
        assert original == {"a": 1, "b": 2}

    def test_deep_update_overwrites_existing(self):
        """Test that existing values are overwritten."""
        original = {"a": 1}
        deep_update(original, {"a": 2})
        assert original == {"a": 2}

    def test_deep_update_nested(self):
        """Test deep updating nested structures."""
        original = {"a": {"b": 1, "c": 2}}
        deep_update(original, {"a": {"b": 10}})
        assert original == {"a": {"b": 10, "c": 2}}

    def test_deep_update_adds_nested_keys(self):
        """Test adding new nested keys."""
        original = {"a": {"b": 1}}
        deep_update(original, {"a": {"c": 2}})
        assert original == {"a": {"b": 1, "c": 2}}

    def test_deep_update_with_both_updates_and_kwargs(self):
        """Test updating with both updates dict and kwargs."""
        original = {"a": 1}
        deep_update(original, {"b": 2}, c=3)
        assert original == {"a": 1, "b": 2, "c": 3}


class TestSetDefaults:
    """Test the set_defaults function."""

    def test_set_defaults_empty(self):
        """Test setting defaults with empty defaults."""
        original = {"a": 1}
        set_defaults(original)
        assert original == {"a": 1}

    def test_set_defaults_adds_missing_keys(self):
        """Test that missing keys are added."""
        original = {"a": 1}
        set_defaults(original, {"b": 2})
        assert original == {"a": 1, "b": 2}

    def test_set_defaults_does_not_overwrite(self):
        """Test that existing values are not overwritten."""
        original = {"a": 1}
        set_defaults(original, {"a": 2})
        assert original == {"a": 1}

    def test_set_defaults_with_kwargs(self):
        """Test setting defaults with kwargs."""
        original = {"a": 1}
        set_defaults(original, b=2)
        assert original == {"a": 1, "b": 2}

    def test_set_defaults_nested(self):
        """Test setting defaults in nested structures."""
        original = {"a": {"b": 1}}
        set_defaults(original, {"a": {"c": 2}})
        assert original == {"a": {"b": 1, "c": 2}}

    def test_set_defaults_nested_does_not_overwrite(self):
        """Test that nested values are not overwritten."""
        original = {"a": {"b": 1}}
        set_defaults(original, {"a": {"b": 2}})
        assert original == {"a": {"b": 1}}

    def test_set_defaults_with_both_defaults_and_kwargs(self):
        """Test setting defaults with both defaults dict and kwargs."""
        original = {"a": 1}
        set_defaults(original, {"b": 2}, c=3)
        assert original == {"a": 1, "b": 2, "c": 3}

    def test_set_defaults_none_defaults(self):
        """Test with None as defaults."""
        original = {"a": 1}
        set_defaults(original, None, b=2)
        assert original == {"a": 1, "b": 2}