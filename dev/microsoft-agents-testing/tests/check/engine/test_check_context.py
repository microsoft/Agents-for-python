"""
Unit tests for the CheckContext class.

This module tests:
- CheckContext initialization
- path tracking
- root actual/baseline references
- child context creation
"""

import pytest
from microsoft_agents.testing.check.engine.check_context import CheckContext
from microsoft_agents.testing.check.engine.types import SafeObject


# =============================================================================
# CheckContext Initialization Tests
# =============================================================================

class TestCheckContextInit:
    """Test CheckContext initialization."""
    
    def test_init_with_safe_object(self):
        actual = SafeObject({"name": "test"})
        baseline = {"name": "test"}
        ctx = CheckContext(actual, baseline)
        
        assert ctx.actual == actual
        assert ctx.baseline == baseline
    
    def test_init_sets_empty_path(self):
        actual = SafeObject({})
        baseline = {}
        ctx = CheckContext(actual, baseline)
        
        assert ctx.path == []
    
    def test_init_sets_root_references(self):
        actual = SafeObject({"key": "value"})
        baseline = {"key": "value"}
        ctx = CheckContext(actual, baseline)
        
        assert ctx.root_actual == actual
        assert ctx.root_baseline == baseline


# =============================================================================
# Child Context Tests
# =============================================================================

class TestCheckContextChild:
    """Test the child context creation."""
    
    def test_child_with_string_key(self):
        actual = SafeObject({"nested": {"value": 42}})
        baseline = {"nested": {"value": 42}}
        ctx = CheckContext(actual, baseline)
        
        child_ctx = ctx.child("nested")
        
        assert child_ctx.path == ["nested"]
        assert child_ctx.baseline == {"value": 42}
    
    def test_child_with_int_key(self):
        actual = SafeObject({"items": [10, 20, 30]})
        baseline = {"items": [10, 20, 30]}
        ctx = CheckContext(actual, baseline)
        
        # First get items child
        items_ctx = ctx.child("items")
        # Then get first item
        item_ctx = items_ctx.child(0)
        
        assert item_ctx.path == ["items", 0]
        assert item_ctx.baseline == 10
    
    def test_child_preserves_root(self):
        actual = SafeObject({"a": {"b": {"c": "deep"}}})
        baseline = {"a": {"b": {"c": "deep"}}}
        ctx = CheckContext(actual, baseline)
        
        child_a = ctx.child("a")
        child_b = child_a.child("b")
        child_c = child_b.child("c")
        
        assert child_c.root_actual == actual
        assert child_c.root_baseline == baseline
    
    def test_child_path_accumulates(self):
        actual = SafeObject({"level1": {"level2": {"level3": "value"}}})
        baseline = {"level1": {"level2": {"level3": "value"}}}
        ctx = CheckContext(actual, baseline)
        
        child1 = ctx.child("level1")
        child2 = child1.child("level2")
        child3 = child2.child("level3")
        
        assert child1.path == ["level1"]
        assert child2.path == ["level1", "level2"]
        assert child3.path == ["level1", "level2", "level3"]


# =============================================================================
# Nested Structure Tests
# =============================================================================

class TestCheckContextNestedStructures:
    """Test CheckContext with various nested structures."""
    
    def test_dict_of_lists(self):
        actual = SafeObject({"scores": [85, 90, 88]})
        baseline = {"scores": [85, 90, 88]}
        ctx = CheckContext(actual, baseline)
        
        scores_ctx = ctx.child("scores")
        assert scores_ctx.path == ["scores"]
        
        first_score_ctx = scores_ctx.child(0)
        assert first_score_ctx.path == ["scores", 0]
        assert first_score_ctx.baseline == 85
    
    def test_list_of_dicts(self):
        actual = SafeObject({"users": [{"name": "Alice"}, {"name": "Bob"}]})
        baseline = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        ctx = CheckContext(actual, baseline)
        
        users_ctx = ctx.child("users")
        first_user_ctx = users_ctx.child(0)
        name_ctx = first_user_ctx.child("name")
        
        assert name_ctx.path == ["users", 0, "name"]
        assert name_ctx.baseline == "Alice"


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestCheckContextEdgeCases:
    """Test edge cases for CheckContext."""
    
    def test_empty_dict(self):
        actual = SafeObject({})
        baseline = {}
        ctx = CheckContext(actual, baseline)
        
        assert ctx.path == []
        assert ctx.baseline == {}
    
    def test_none_values(self):
        actual = SafeObject({"value": None})
        baseline = {"value": None}
        ctx = CheckContext(actual, baseline)
        
        value_ctx = ctx.child("value")
        assert value_ctx.baseline is None
    
    def test_deep_nesting(self):
        deep_dict = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        actual = SafeObject(deep_dict)
        ctx = CheckContext(actual, deep_dict)
        
        current = ctx
        for key in ["a", "b", "c", "d", "e"]:
            current = current.child(key)
        
        assert current.path == ["a", "b", "c", "d", "e"]
        assert current.baseline == "deep"
