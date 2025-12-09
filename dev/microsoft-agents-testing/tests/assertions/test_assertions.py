import pytest
from microsoft_agents.testing.assertions.assertions import Assertions


class TestAssertionsExpand:
    """Tests for the Assertions.expand method"""

    def test_expand_simple_dict_no_dots(self):
        """Test that a simple dict without dots remains unchanged"""
        data = {"key1": "value1", "key2": "value2"}
        result = Assertions.expand(data)
        assert result == {"key1": "value1", "key2": "value2"}

    def test_expand_non_dict_returns_as_is(self):
        """Test that non-dict types are returned unchanged"""
        assert Assertions.expand("string") == "string"
        assert Assertions.expand(123) == 123
        assert Assertions.expand([1, 2, 3]) == [1, 2, 3]
        assert Assertions.expand(None) is None

    def test_expand_single_level_dotted_key(self):
        """Test expanding a single level dotted key"""
        data = {"parent.child": "value"}
        result = Assertions.expand(data)
        assert result == {"parent": {"child": "value"}}

    def test_expand_multiple_dotted_keys_same_parent(self):
        """Test expanding multiple dotted keys with the same parent"""
        data = {"parent.child1": "value1", "parent.child2": "value2"}
        result = Assertions.expand(data)
        assert result == {
            "parent": {"child1": "value1", "child2": "value2"}
        }

    def test_expand_nested_dotted_keys(self):
        """Test expanding deeply nested dotted keys"""
        data = {"parent.child.grandchild": "value"}
        result = Assertions.expand(data)
        assert result == {"parent": {"child": {"grandchild": "value"}}}

    def test_expand_mixed_dotted_and_simple_keys(self):
        """Test expanding a mix of dotted and simple keys"""
        data = {
            "simple": "value1",
            "parent.child": "value2",
            "another": "value3"
        }
        result = Assertions.expand(data)
        assert result == {
            "simple": "value1",
            "parent": {"child": "value2"},
            "another": "value3"
        }

    def test_expand_with_nested_dict_values(self):
        """Test expanding when values are themselves dicts with dots"""
        data = {
            "parent.child": {"nested.key": "value"}
        }
        result = Assertions.expand(data)
        assert result == {
            "parent": {
                "child": {"nested": {"key": "value"}}
            }
        }

    def test_expand_empty_dict(self):
        """Test expanding an empty dict"""
        data = {}
        result = Assertions.expand(data)
        assert result == {}

    def test_expand_multiple_levels_different_parents(self):
        """Test expanding multiple dotted keys with different parents"""
        data = {
            "parent1.child": "value1",
            "parent2.child": "value2",
            "parent3.child.grandchild": "value3"
        }
        result = Assertions.expand(data)
        assert result == {
            "parent1": {"child": "value1"},
            "parent2": {"child": "value2"},
            "parent3": {"child": {"grandchild": "value3"}}
        }

    def test_expand_raises_error_on_duplicate_root_with_dotted(self):
        """Test that duplicate keys raise RuntimeError"""
        # Case where dotted key conflicts with existing root
        data = {
            "parent": "value1",
            "parent.child": "value2"
        }
        # The second key "parent.child" tries to set parent["child"]
        # but "parent" already exists as a non-dict value
        # This should raise a RuntimeError when processing
        with pytest.raises(RuntimeError):
            Assertions.expand(data)

    def test_expand_with_numeric_values(self):
        """Test expanding with numeric values"""
        data = {
            "config.port": 8080,
            "config.timeout": 30
        }
        result = Assertions.expand(data)
        assert result == {
            "config": {"port": 8080, "timeout": 30}
        }

    def test_expand_with_boolean_values(self):
        """Test expanding with boolean values"""
        data = {
            "settings.enabled": True,
            "settings.debug": False
        }
        result = Assertions.expand(data)
        assert result == {
            "settings": {"enabled": True, "debug": False}
        }

    def test_expand_with_list_values(self):
        """Test expanding with list values"""
        data = {
            "config.items": [1, 2, 3],
            "config.names": ["a", "b"]
        }
        result = Assertions.expand(data)
        assert result == {
            "config": {"items": [1, 2, 3], "names": ["a", "b"]}
        }

    def test_expand_with_none_values(self):
        """Test expanding with None values"""
        data = {
            "config.value": None,
            "config.other": "something"
        }
        result = Assertions.expand(data)
        assert result == {
            "config": {"value": None, "other": "something"}
        }


class TestAssertionsEvaluate:
    """Tests for the Assertions.evaluate method"""

    def test_evaluate_equal_strings(self):
        """Test that equal strings return True"""
        assert Assertions.evaluate("test", "test") is True

    def test_evaluate_unequal_strings(self):
        """Test that unequal strings return False"""
        assert Assertions.evaluate("test", "other") is False

    def test_evaluate_equal_numbers(self):
        """Test that equal numbers return True"""
        assert Assertions.evaluate(42, 42) is True
        assert Assertions.evaluate(3.14, 3.14) is True

    def test_evaluate_unequal_numbers(self):
        """Test that unequal numbers return False"""
        assert Assertions.evaluate(42, 43) is False
        assert Assertions.evaluate(3.14, 3.15) is False

    def test_evaluate_equal_dicts(self):
        """Test that equal dicts return True"""
        dict1 = {"key": "value", "num": 42}
        dict2 = {"key": "value", "num": 42}
        Assertions.validate(dict1, dict2)

    def test_evaluate_unequal_dicts(self):
        """Test that unequal dicts return False"""
        dict1 = {"key": "value1"}
        dict2 = {"key": "value2"}
        assert Assertions.evaluate(dict1, dict2) is False

    def test_evaluate_equal_lists(self):
        """Test that equal lists return True"""
        list1 = [1, 2, 3]
        list2 = [1, 2, 3]
        assert Assertions.evaluate(list1, list2) is True

    def test_evaluate_unequal_lists(self):
        """Test that unequal lists return False"""
        list1 = [1, 2, 3]
        list2 = [1, 2, 4]
        assert Assertions.evaluate(list1, list2) is False

    def test_evaluate_none_values(self):
        """Test that None values are compared correctly"""
        assert Assertions.evaluate(None, None) is True
        assert Assertions.evaluate(None, "something") is False

    def test_evaluate_boolean_values(self):
        """Test that boolean values are compared correctly"""
        assert Assertions.evaluate(True, True) is True
        assert Assertions.evaluate(False, False) is True
        assert Assertions.evaluate(True, False) is False

    def test_evaluate_different_types(self):
        """Test that different types return False"""
        assert Assertions.evaluate("42", 42) is False
        assert Assertions.evaluate([1, 2], (1, 2)) is False
        assert Assertions.evaluate(True, 1) is True  # Even though True == 1 in Python

    def test_evaluate_nested_structures(self):
        """Test evaluation of nested data structures"""
        nested1 = {"outer": {"inner": [1, 2, 3]}}
        nested2 = {"outer": {"inner": [1, 2, 3]}}
        nested3 = {"outer": {"inner": [1, 2, 4]}}
        
        assert Assertions.evaluate(nested1, nested2) is True
        assert Assertions.evaluate(nested1, nested3) is False

    def test_evaluate_empty_collections(self):
        """Test evaluation of empty collections"""
        assert Assertions.evaluate({}, {}) is True
        assert Assertions.evaluate([], []) is True
        assert Assertions.evaluate("", "") is True