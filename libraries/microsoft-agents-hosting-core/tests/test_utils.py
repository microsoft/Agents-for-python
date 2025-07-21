from microsoft.agents.hosting.core.storage.storage_test_utils import (
    MockStoreItem,
    MockStoreItemB,
    my_deepcopy,
    subsets,
)


def eq_helper(a, b):
    def key(x):
        return str(x)

    return sorted(a, key=key) == sorted(b, key=key)


def test_eq_helper():

    a1 = [{"a": 1}, {"b": 2}, {"c": 3}]
    a2 = [{"c": 3}, {"b": 2}, {"a": 1}]
    assert eq_helper(a1, a2)

    a1 = [[2], [3], [4], [3]]
    a2 = [[4], [3], [5], [2]]
    assert not eq_helper(a1, a2)

    a1 = [["a"], [3], [4], [3]]
    a2 = [[4], [3], [3], ["a"]]
    assert eq_helper(a1, a2)


def test_my_deepcopy():
    original = {
        "a": MockStoreItem({"id": "a", "value": 1}),
        "b": {
            "b1": MockStoreItemB({"key": "b1"}, other_field=False),
            "b2": [1, 2, 3],
            "b3": {"nested": MockStoreItem({"id": "nested", "value": 42})},
        },
        "c": [
            MockStoreItem({"id": "c1"}),
            MockStoreItemB({"id": "c2"}, other_field=True),
        ],
        "d": "just a string",
        "e": 12345,
    }
    copy = my_deepcopy(original)
    assert copy == original
    assert copy is not original
    assert copy["a"] is not original["a"]
    assert copy["b"] is not original["b"]
    assert copy["b"]["b1"] is not original["b"]["b1"]
    assert copy["b"]["b3"] is not original["b"]["b3"]
    assert copy["b"]["b3"]["nested"] is not original["b"]["b3"]["nested"]
    assert copy["c"] is not original["c"]
    assert copy["c"][0] is not original["c"][0]
    assert copy["c"][1] is not original["c"][1]
    assert copy["d"] == original["d"]
    assert copy["e"] == original["e"]


def test_subsets():
    assert eq_helper(
        subsets(
            ["a", "b", "c"],
            -1,
        ),
        [["a"], ["a", "b"], ["a", "b", "c"], ["b"], ["b", "c"], ["c"]],
    )
    assert eq_helper(
        subsets(["a", "b", "c"]),
        [["a"], ["a", "b"], ["a", "b", "c"], ["b"], ["b", "c"], ["c"]],
    )


def test_subsets_0():
    assert subsets(["a", "b", "c", "d"], 0) == []


def test_subsets_1():
    assert eq_helper(subsets(["a", "b", "c", 3, 2], 1), [["a"], ["b"], ["c"], [3], [2]])


def test_subsets_2():
    assert eq_helper(
        subsets(["a", "b", "c"], 2), [["a"], ["b"], ["c"], ["a", "b"], ["b", "c"]]
    )


def test_subsets_3():
    assert eq_helper(
        subsets(["a", "b", "c"]),
        [["a"], ["a", "b"], ["a", "b", "c"], ["b"], ["b", "c"], ["c"]],
    )
