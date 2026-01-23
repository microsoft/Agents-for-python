"""
Unit tests for the underscore models module.
"""

import pytest
from microsoft_agents.testing.underscore.models import (
    OperationType,
    PlaceholderType,
    PlaceholderInfo,
)


class TestOperationType:
    """Test the OperationType enum."""
    
    def test_all_operation_types_exist(self):
        assert OperationType.BINARY_OP
        assert OperationType.UNARY_OP
        assert OperationType.GETATTR
        assert OperationType.GETITEM
        assert OperationType.CALL
        assert OperationType.RBINARY_OP
    
    def test_operation_types_are_distinct(self):
        types = [
            OperationType.BINARY_OP,
            OperationType.UNARY_OP,
            OperationType.GETATTR,
            OperationType.GETITEM,
            OperationType.CALL,
            OperationType.RBINARY_OP,
        ]
        assert len(types) == len(set(types))
    
    def test_operation_type_count(self):
        assert len(OperationType) == 6


class TestPlaceholderType:
    """Test the PlaceholderType enum."""
    
    def test_all_placeholder_types_exist(self):
        assert PlaceholderType.ANONYMOUS
        assert PlaceholderType.INDEXED
        assert PlaceholderType.NAMED
        assert PlaceholderType.EXPR
    
    def test_placeholder_types_are_distinct(self):
        types = [
            PlaceholderType.ANONYMOUS,
            PlaceholderType.INDEXED,
            PlaceholderType.NAMED,
            PlaceholderType.EXPR,
        ]
        assert len(types) == len(set(types))
    
    def test_placeholder_type_count(self):
        assert len(PlaceholderType) == 4


class TestPlaceholderInfo:
    """Test the PlaceholderInfo dataclass."""
    
    def test_creation_with_all_fields(self):
        info = PlaceholderInfo(
            anonymous_count=2,
            indexed={0, 1, 2},
            named={"x", "y"},
        )
        assert info.anonymous_count == 2
        assert info.indexed == {0, 1, 2}
        assert info.named == {"x", "y"}
    
    def test_creation_with_empty_sets(self):
        info = PlaceholderInfo(
            anonymous_count=0,
            indexed=set(),
            named=set(),
        )
        assert info.anonymous_count == 0
        assert info.indexed == set()
        assert info.named == set()
    
    def test_total_positional_needed_anonymous_only(self):
        info = PlaceholderInfo(
            anonymous_count=3,
            indexed=set(),
            named=set(),
        )
        assert info.total_positional_needed == 3
    
    def test_total_positional_needed_indexed_only(self):
        info = PlaceholderInfo(
            anonymous_count=0,
            indexed={0, 2, 5},
            named=set(),
        )
        # Highest index is 5, so need 6 positional args
        assert info.total_positional_needed == 6
    
    def test_total_positional_needed_anonymous_higher(self):
        info = PlaceholderInfo(
            anonymous_count=5,
            indexed={0, 1},
            named=set(),
        )
        # anonymous_count (5) > max_indexed + 1 (2)
        assert info.total_positional_needed == 5
    
    def test_total_positional_needed_indexed_higher(self):
        info = PlaceholderInfo(
            anonymous_count=2,
            indexed={0, 9},
            named=set(),
        )
        # max_indexed + 1 (10) > anonymous_count (2)
        assert info.total_positional_needed == 10
    
    def test_total_positional_needed_equal(self):
        info = PlaceholderInfo(
            anonymous_count=3,
            indexed={0, 1, 2},
            named=set(),
        )
        # Both are 3
        assert info.total_positional_needed == 3
    
    def test_total_positional_needed_empty(self):
        info = PlaceholderInfo(
            anonymous_count=0,
            indexed=set(),
            named=set(),
        )
        assert info.total_positional_needed == 0
    
    def test_total_positional_needed_ignores_named(self):
        info = PlaceholderInfo(
            anonymous_count=1,
            indexed=set(),
            named={"x", "y", "z"},
        )
        # Named placeholders don't affect positional count
        assert info.total_positional_needed == 1


class TestPlaceholderInfoRepr:
    """Test the __repr__ method of PlaceholderInfo."""
    
    def test_repr_with_all_fields(self):
        info = PlaceholderInfo(
            anonymous_count=2,
            indexed={0, 1},
            named={"x"},
        )
        r = repr(info)
        assert "PlaceholderInfo" in r
        assert "anonymous=2" in r
        assert "indexed=" in r
        assert "named=" in r
    
    def test_repr_anonymous_only(self):
        info = PlaceholderInfo(
            anonymous_count=3,
            indexed=set(),
            named=set(),
        )
        r = repr(info)
        assert "PlaceholderInfo" in r
        assert "anonymous=3" in r
        assert "indexed" not in r
        assert "named" not in r
    
    def test_repr_indexed_only(self):
        info = PlaceholderInfo(
            anonymous_count=0,
            indexed={0, 1, 2},
            named=set(),
        )
        r = repr(info)
        assert "PlaceholderInfo" in r
        assert "anonymous" not in r
        assert "indexed=" in r
        assert "named" not in r
    
    def test_repr_named_only(self):
        info = PlaceholderInfo(
            anonymous_count=0,
            indexed=set(),
            named={"x", "y"},
        )
        r = repr(info)
        assert "PlaceholderInfo" in r
        assert "anonymous" not in r
        assert "indexed" not in r
        assert "named=" in r
    
    def test_repr_empty(self):
        info = PlaceholderInfo(
            anonymous_count=0,
            indexed=set(),
            named=set(),
        )
        r = repr(info)
        assert r == "PlaceholderInfo()"
    
    def test_repr_anonymous_and_named(self):
        info = PlaceholderInfo(
            anonymous_count=1,
            indexed=set(),
            named={"key"},
        )
        r = repr(info)
        assert "anonymous=1" in r
        assert "named=" in r
        assert "indexed" not in r


class TestPlaceholderInfoEquality:
    """Test equality comparison of PlaceholderInfo (dataclass default)."""
    
    def test_equal_instances(self):
        info1 = PlaceholderInfo(
            anonymous_count=2,
            indexed={0, 1},
            named={"x"},
        )
        info2 = PlaceholderInfo(
            anonymous_count=2,
            indexed={0, 1},
            named={"x"},
        )
        assert info1 == info2
    
    def test_different_anonymous_count(self):
        info1 = PlaceholderInfo(anonymous_count=1, indexed=set(), named=set())
        info2 = PlaceholderInfo(anonymous_count=2, indexed=set(), named=set())
        assert info1 != info2
    
    def test_different_indexed(self):
        info1 = PlaceholderInfo(anonymous_count=0, indexed={0}, named=set())
        info2 = PlaceholderInfo(anonymous_count=0, indexed={1}, named=set())
        assert info1 != info2
    
    def test_different_named(self):
        info1 = PlaceholderInfo(anonymous_count=0, indexed=set(), named={"x"})
        info2 = PlaceholderInfo(anonymous_count=0, indexed=set(), named={"y"})
        assert info1 != info2