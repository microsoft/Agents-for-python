# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from copy import copy

import pytest

from microsoft_agents.activity.config._engine._path.types import _UserDict, _UserList


@pytest.mark.parametrize("make_copy", [True, False])
def test_user_dict_controls_backing_mapping_ownership(make_copy):
    source = {"Value": 1}
    wrapped = _UserDict(source, make_copy)

    wrapped["Other"] = 2

    assert ("Other" in source) is not make_copy
    assert wrapped["Other"] == 2


def test_user_dict_missing_hook_is_not_used_by_get_or_membership():
    class WithMissing(_UserDict):
        def __missing__(self, key):
            return f"missing:{key}"

    wrapped = WithMissing()

    assert wrapped["Value"] == "missing:Value"
    assert wrapped.get("Value", 7) == 7
    assert "Value" not in wrapped


@pytest.mark.parametrize("factory", [copy, lambda value: value.copy()])
def test_user_dict_subclass_copy_preserves_metadata_and_isolates_top_level(factory):
    class Derived(_UserDict):
        pass

    nested = {}
    source = Derived({"Nested": nested})
    source.label = "config"

    cloned = factory(source)
    cloned["Other"] = 2

    assert isinstance(cloned, Derived)
    assert cloned.label == "config"
    assert cloned["Nested"] is nested
    assert "Other" not in source


@pytest.mark.parametrize(
    "factory",
    [
        copy,
        lambda value: value.copy(),
        lambda value: value[:],
        lambda value: value + [],
        lambda value: [] + value,
        lambda value: value * 2,
    ],
)
def test_user_list_factories_preserve_subclass_and_isolate_backing_list(factory):
    class Derived(_UserList):
        pass

    nested = {}
    source = Derived([nested])

    cloned = factory(source)
    cloned.append("other")

    assert isinstance(cloned, Derived)
    assert cloned[0] is nested
    assert len(source) == 1


def test_user_list_accepts_generators_and_copies_input_storage():
    source = [1, 2]
    wrapped = _UserList(source)
    generated = _UserList(item for item in source)

    wrapped.append(3)

    assert source == [1, 2]
    assert generated == [1, 2]


@pytest.mark.parametrize("operation", ["iadd", "imul"])
def test_user_list_in_place_operators_preserve_identity_and_nested_aliases(operation):
    nested = {"Value": 7}
    wrapped = _UserList([nested])
    original = wrapped

    if operation == "iadd":
        wrapped += wrapped
    else:
        wrapped *= 2

    assert wrapped is original
    assert len(wrapped) == 2
    assert wrapped[0] is wrapped[1] is nested


def test_user_dict_failed_subclass_copy_restores_original_storage():
    class FailingCopy(_UserDict):
        def __copy__(self):
            raise RuntimeError("copy failed")

    source = FailingCopy({"Value": 7})

    with pytest.raises(RuntimeError, match="copy failed"):
        source.copy()

    assert dict(source) == {"Value": 7}
    source["Other"] = 8
    assert dict(source) == {"Value": 7, "Other": 8}
