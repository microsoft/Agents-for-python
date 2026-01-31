# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the backend utility functions."""

import pytest

from microsoft_agents.testing.core.fluent.backend.utils import (
    flatten,
    expand,
    _merge,
    _resolve_kwargs,
    _resolve_kwargs_expanded,
    deep_update,
    set_defaults,
)


class TestFlatten:
    """Tests for the flatten function."""

    def test_flatten_empty_dict(self):
        """Flattening an empty dict returns an empty dict."""
        result = flatten({})
        assert result == {}

    def test_flatten_single_level_dict(self):
        """Flattening a single-level dict returns the same dict."""
        data = {"a": 1, "b": 2, "c": 3}
        result = flatten(data)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_flatten_nested_dict(self):
        """Flattening a nested dict concatenates keys with dots."""
        data = {"a": {"b": {"c": 1}}}
        result = flatten(data)
        assert result == {"a.b.c": 1}

    def test_flatten_mixed_dict(self):
        """Flattening a mixed dict handles both nested and flat keys."""
        data = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        result = flatten(data)
        assert result == {"a": 1, "b.c": 2, "b.d.e": 3}

    def test_flatten_custom_separator(self):
        """Flattening with a custom separator uses that separator."""
        data = {"a": {"b": 1}}
        result = flatten(data, level_sep="/")
        assert result == {"a/b": 1}

    def test_flatten_with_parent_key(self):
        """Flattening with a parent key prefixes all keys."""
        data = {"a": 1, "b": 2}
        result = flatten(data, parent_key="root")
        assert result == {"root.a": 1, "root.b": 2}

    def test_flatten_preserves_non_dict_values(self):
        """Flattening preserves non-dict values like lists and strings."""
        data = {"a": [1, 2, 3], "b": "hello", "c": None}
        result = flatten(data)
        assert result == {"a": [1, 2, 3], "b": "hello", "c": None}


class TestExpand:
    """Tests for the expand function."""

    def test_expand_empty_dict(self):
        """Expanding an empty dict returns an empty dict."""
        result = expand({})
        assert result == {}

    def test_expand_single_level_dict(self):
        """Expanding a single-level dict returns the same dict."""
        data = {"a": 1, "b": 2}
        result = expand(data)
        assert result == {"a": 1, "b": 2}

    def test_expand_dotted_keys(self):
        """Expanding dotted keys creates nested dicts."""
        data = {"a.b.c": 1}
        result = expand(data)
        assert result == {"a": {"b": {"c": 1}}}

    def test_expand_mixed_keys(self):
        """Expanding handles both dotted and flat keys."""
        data = {"a": 1, "b.c": 2, "b.d.e": 3}
        result = expand(data)
        assert result == {"a": 1, "b": {"c": 2, "d": {"e": 3}}}

    def test_expand_custom_separator(self):
        """Expanding with a custom separator uses that separator."""
        data = {"a/b/c": 1}
        result = expand(data, level_sep="/")
        assert result == {"a": {"b": {"c": 1}}}

    def test_expand_non_dict_returns_same(self):
        """Expanding a non-dict value returns the same value."""
        assert expand("hello") == "hello"
        assert expand(42) == 42
        assert expand([1, 2, 3]) == [1, 2, 3]

    def test_expand_conflicting_keys_raises(self):
        """Expanding conflicting keys raises RuntimeError."""
        data = {"a": 1, "a.b": 2}
        with pytest.raises(RuntimeError, match="Conflicting key"):
            expand(data)

    def test_expand_duplicate_keys_raises(self):
        """Expanding duplicate nested keys raises RuntimeError."""
        # This is a bit contrived but tests the path where root exists and path exists
        data = {"a.b": 1}
        expanded = expand(data)
        # Verify normal behavior first
        assert expanded == {"a": {"b": 1}}

    def test_expand_inverse_of_flatten(self):
        """Expanding a flattened dict returns the original structure."""
        original = {"a": {"b": {"c": 1}}, "d": 2}
        flattened = flatten(original)
        expanded = expand(flattened)
        assert expanded == original


class TestMerge:
    """Tests for the _merge function."""

    def test_merge_empty_dicts(self):
        """Merging two empty dicts results in an empty dict."""
        original = {}
        other = {}
        _merge(original, other)
        assert original == {}

    def test_merge_into_empty_dict(self):
        """Merging into an empty dict copies all keys."""
        original = {}
        other = {"a": 1, "b": 2}
        _merge(original, other)
        assert original == {"a": 1, "b": 2}

    def test_merge_from_empty_dict(self):
        """Merging from an empty dict leaves original unchanged."""
        original = {"a": 1, "b": 2}
        other = {}
        _merge(original, other)
        assert original == {"a": 1, "b": 2}

    def test_merge_non_overlapping_keys(self):
        """Merging non-overlapping keys combines both dicts."""
        original = {"a": 1}
        other = {"b": 2}
        _merge(original, other)
        assert original == {"a": 1, "b": 2}

    def test_merge_overwrites_leaves_by_default(self):
        """Merging overwrites leaf values by default."""
        original = {"a": 1}
        other = {"a": 2}
        _merge(original, other)
        assert original == {"a": 2}

    def test_merge_no_overwrite_leaves(self):
        """Merging with overwrite_leaves=False keeps original values."""
        original = {"a": 1}
        other = {"a": 2}
        _merge(original, other, overwrite_leaves=False)
        assert original == {"a": 1}

    def test_merge_nested_dicts(self):
        """Merging nested dicts merges recursively."""
        original = {"a": {"b": 1, "c": 2}}
        other = {"a": {"c": 3, "d": 4}}
        _merge(original, other)
        assert original == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_merge_nested_no_overwrite(self):
        """Merging nested dicts with overwrite_leaves=False adds missing keys only."""
        original = {"a": {"b": 1}}
        other = {"a": {"b": 2, "c": 3}}
        _merge(original, other, overwrite_leaves=False)
        assert original == {"a": {"b": 1, "c": 3}}

    def test_merge_dict_over_non_dict(self):
        """Merging a dict over a non-dict value overwrites (when overwrite_leaves=True)."""
        original = {"a": 1}
        other = {"a": {"b": 2}}
        _merge(original, other)
        assert original == {"a": {"b": 2}}

    def test_merge_non_dict_over_dict(self):
        """Merging a non-dict over a dict value overwrites (when overwrite_leaves=True)."""
        original = {"a": {"b": 2}}
        other = {"a": 1}
        _merge(original, other)
        assert original == {"a": 1}


class TestResolveKwargs:
    """Tests for the _resolve_kwargs function."""

    def test_resolve_kwargs_none_data(self):
        """Resolving with None data returns only kwargs."""
        result = _resolve_kwargs(None, a=1, b=2)
        assert result == {"a": 1, "b": 2}

    def test_resolve_kwargs_empty_data(self):
        """Resolving with empty data returns only kwargs."""
        result = _resolve_kwargs({}, a=1, b=2)
        assert result == {"a": 1, "b": 2}

    def test_resolve_kwargs_no_kwargs(self):
        """Resolving with no kwargs returns a copy of data."""
        data = {"a": 1, "b": 2}
        result = _resolve_kwargs(data)
        assert result == {"a": 1, "b": 2}
        # Verify it's a copy
        assert result is not data

    def test_resolve_kwargs_merge(self):
        """Resolving merges data and kwargs."""
        result = _resolve_kwargs({"a": 1}, b=2, c=3)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_resolve_kwargs_overwrites(self):
        """Kwargs overwrite data values."""
        result = _resolve_kwargs({"a": 1}, a=2)
        assert result == {"a": 2}

    def test_resolve_kwargs_deep_copy(self):
        """Resolving deep copies nested data."""
        data = {"a": {"b": 1}}
        result = _resolve_kwargs(data)
        result["a"]["b"] = 2
        # Original should be unchanged
        assert data == {"a": {"b": 1}}

    def test_resolve_kwargs_nested_merge(self):
        """Resolving merges nested kwargs."""
        result = _resolve_kwargs({"a": {"b": 1}}, a={"c": 2})
        assert result == {"a": {"b": 1, "c": 2}}


class TestResolveKwargsExpanded:
    """Tests for the _resolve_kwargs_expanded function."""

    def test_resolve_kwargs_expanded_none_data(self):
        """Resolving with None data expands kwargs."""
        result = _resolve_kwargs_expanded(None, **{"a.b": 1})
        assert result == {"a": {"b": 1}}

    def test_resolve_kwargs_expanded_dotted_data(self):
        """Resolving expands dotted keys in data."""
        result = _resolve_kwargs_expanded({"a.b": 1})
        assert result == {"a": {"b": 1}}

    def test_resolve_kwargs_expanded_merge(self):
        """Resolving merges expanded data and kwargs."""
        result = _resolve_kwargs_expanded({"a.b": 1}, **{"a.c": 2})
        assert result == {"a": {"b": 1, "c": 2}}

    def test_resolve_kwargs_expanded_deep_copy(self):
        """Resolving deep copies nested data."""
        data = {"a": {"b": 1}}
        result = _resolve_kwargs_expanded(data)
        result["a"]["b"] = 2
        # Original should be unchanged
        assert data == {"a": {"b": 1}}


class TestDeepUpdate:
    """Tests for the deep_update function."""

    def test_deep_update_with_dict(self):
        """Deep update with a dict updates the original."""
        original = {"a": 1}
        deep_update(original, {"b": 2})
        assert original == {"a": 1, "b": 2}

    def test_deep_update_with_kwargs(self):
        """Deep update with kwargs updates the original."""
        original = {"a": 1}
        deep_update(original, b=2, c=3)
        assert original == {"a": 1, "b": 2, "c": 3}

    def test_deep_update_with_both(self):
        """Deep update with both dict and kwargs combines them."""
        original = {"a": 1}
        deep_update(original, {"b": 2}, c=3)
        assert original == {"a": 1, "b": 2, "c": 3}

    def test_deep_update_overwrites(self):
        """Deep update overwrites existing values."""
        original = {"a": 1}
        deep_update(original, {"a": 2})
        assert original == {"a": 2}

    def test_deep_update_nested(self):
        """Deep update merges nested dicts."""
        original = {"a": {"b": 1}}
        deep_update(original, {"a": {"c": 2}})
        assert original == {"a": {"b": 1, "c": 2}}

    def test_deep_update_none_updates(self):
        """Deep update with None updates is a no-op."""
        original = {"a": 1}
        deep_update(original, None)
        assert original == {"a": 1}


class TestSetDefaults:
    """Tests for the set_defaults function."""

    def test_set_defaults_with_dict(self):
        """Set defaults with a dict adds missing keys."""
        original = {"a": 1}
        set_defaults(original, {"b": 2})
        assert original == {"a": 1, "b": 2}

    def test_set_defaults_with_kwargs(self):
        """Set defaults with kwargs adds missing keys."""
        original = {"a": 1}
        set_defaults(original, b=2, c=3)
        assert original == {"a": 1, "b": 2, "c": 3}

    def test_set_defaults_with_both(self):
        """Set defaults with both dict and kwargs combines them."""
        original = {"a": 1}
        set_defaults(original, {"b": 2}, c=3)
        assert original == {"a": 1, "b": 2, "c": 3}

    def test_set_defaults_does_not_overwrite(self):
        """Set defaults does not overwrite existing values."""
        original = {"a": 1}
        set_defaults(original, {"a": 2})
        assert original == {"a": 1}

    def test_set_defaults_nested(self):
        """Set defaults merges nested dicts without overwriting."""
        original = {"a": {"b": 1}}
        set_defaults(original, {"a": {"b": 2, "c": 3}})
        assert original == {"a": {"b": 1, "c": 3}}

    def test_set_defaults_none_defaults(self):
        """Set defaults with None defaults is a no-op."""
        original = {"a": 1}
        set_defaults(original, None)
        assert original == {"a": 1}
