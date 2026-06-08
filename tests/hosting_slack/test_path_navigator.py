"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from microsoft_agents.hosting.slack._path_navigator import try_get_path_value


class TestPathNavigator:
    def test_empty_path_returns_root(self):
        data = {"a": 1}
        found, value = try_get_path_value(data, "")
        assert found and value is data

    def test_simple_dot_path(self):
        found, value = try_get_path_value({"a": {"b": "c"}}, "a.b")
        assert found and value == "c"

    def test_array_index(self):
        found, value = try_get_path_value({"a": [10, 20, 30]}, "a[1]")
        assert found and value == 20

    def test_negative_array_index(self):
        found, value = try_get_path_value({"a": [10, 20, 30]}, "a[-1]")
        assert found and value == 30

    def test_nested_array_and_object(self):
        found, value = try_get_path_value(
            {"a": [{"b": [{"c": "deep"}]}]}, "a[0].b[0].c"
        )
        assert found and value == "deep"

    def test_missing_key_returns_not_found(self):
        found, value = try_get_path_value({"a": 1}, "b")
        assert not found and value is None

    def test_out_of_range_index(self):
        found, _ = try_get_path_value({"a": [1, 2]}, "a[5]")
        assert not found

    def test_case_insensitive_fallback(self):
        found, value = try_get_path_value({"FooBar": 7}, "foobar")
        assert found and value == 7

    def test_case_sensitive_takes_precedence(self):
        # Exact match wins even when a case-insensitive sibling exists
        found, value = try_get_path_value({"foo": 1, "FOO": 2}, "foo")
        assert found and value == 1

    def test_unbalanced_brackets_return_not_found(self):
        found, _ = try_get_path_value({"a": [1]}, "a[0")
        assert not found

    def test_primitive_node_property_access_returns_not_found(self):
        found, _ = try_get_path_value({"a": "string"}, "a.length")
        assert not found
