# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config import wildcard
from microsoft_agents.activity.config._engine._path.types import (
    _MISSING,
    _MissingType,
    _Path,
    _SimplePathSegment,
    _Wildcard,
    _is_missing,
)
from microsoft_agents.activity.config._utils import _get_segments, _legpath, _netpath


@pytest.mark.parametrize(
    "ignore_case, ignore_underscores, target, matches",
    [
        (False, False, "Client_Id", True),
        (False, False, "client_id", False),
        (False, False, "ClientId", False),
        (True, False, "CLIENT_ID", True),
        (True, False, "CLIENTID", False),
        (False, True, "ClientId", True),
        (False, True, "clientid", False),
        (True, True, "CLIENTID", True),
        (True, True, "Other", False),
    ],
)
def test_segment_matching_policies(ignore_case, ignore_underscores, target, matches):
    segment = _SimplePathSegment(
        "Client_Id",
        ignore_case=ignore_case,
        ignore_underscores=ignore_underscores,
    )

    assert segment.check(target) is matches
    assert segment.check(_SimplePathSegment(target)) is matches


def test_case_insensitive_matching_uses_unicode_casefold():
    segment = _SimplePathSegment("Straße", ignore_case=True)

    assert segment.check("STRASSE")
    assert segment.folded == "strasse"


@pytest.mark.parametrize(
    "value, target, matches",
    [
        (2, 2, True),
        ("2", "2", True),
        (2, "2", False),
        ("2", 2, False),
        (2, 3, False),
        ("2", "3", False),
    ],
)
def test_numeric_segments_preserve_integer_and_string_key_types(value, target, matches):
    segment = _SimplePathSegment(value)

    assert segment.check(target) is matches
    assert segment.check(_SimplePathSegment(target)) is matches


def test_segment_equality_includes_matching_policy():
    exact = _SimplePathSegment("Name")
    insensitive = _SimplePathSegment("Name", ignore_case=True)

    assert exact == _SimplePathSegment("Name")
    assert exact != insensitive
    assert insensitive.check(exact)
    assert _SimplePathSegment(1) != _SimplePathSegment("1")


def test_path_strings_are_exact_and_reject_embedded_separators():
    with pytest.raises(ValueError, match="must not contain"):
        _Path.create("Section::Value")

    path = _Path.create("Section")

    assert len(path) == 1
    assert path[0].check("Section")
    assert not path[0].check("section")
    assert not _Path("Section", "Value").check(_Path("section", "value"))


def test_path_create_preserves_existing_path_and_segment_policy():
    segment = _SimplePathSegment("Client_Id", ignore_case=True)
    path = _Path(segment, "Value")

    assert _Path.create(path) is path
    assert _Path.create(segment)[0] is segment
    assert path[0] is segment
    assert _Path.create(["Section", "Value"]).check(_Path("Section", "Value"))
    assert _Path.create(2).check(_Path(2))
    assert _Path.create(0).check(_Path(0))


def test_path_slice_and_concatenation_preserve_policies_without_mutating_source():
    path = _Path(_SimplePathSegment("Section", ignore_case=True), "Value")

    sliced = path[:1]
    combined = sliced + _Path("Other")

    assert sliced.check(_Path("SECTION"))
    assert combined.check(_Path("SECTION", "Other"))
    assert not combined.check(_Path("SECTION", "other"))
    assert str(path) == "Section::Value"
    assert str(combined) == "Section::Other"


def test_path_check_requires_equal_length_and_a_path_operand():
    assert not _Path("A").check(_Path("A", "B"))
    with pytest.raises(TypeError, match="Unsupported type"):
        _Path("A").check("A")


@pytest.mark.parametrize("value", [None, {}, object()])
def test_path_create_rejects_unsupported_inputs(value):
    with pytest.raises(TypeError, match="Unsupported type"):
        _Path.create(value)


def test_legacy_and_net_factories_apply_different_underscore_policies():
    legacy = _legpath("CLIENT_ID", "settings")
    net = _netpath("CLIENT_ID", "settings")

    assert legacy.check(_Path("clientid", "SETTINGS"))
    assert net.check(_Path("client_id", "SETTINGS"))
    assert not net.check(_Path("clientid", "SETTINGS"))


@pytest.mark.parametrize(
    "factory, kwargs",
    [
        (_get_segments, {"ignore_case": True, "ignore_underscores": True}),
        (_legpath, {}),
        (_netpath, {}),
    ],
)
def test_path_helpers_preserve_supplied_segment_policies(factory, kwargs):
    exact = _SimplePathSegment("Client_Id")

    segments = factory("PARENT_KEY", exact, **kwargs)
    path = _Path(*segments)

    assert segments[1] is exact
    assert path.check(_Path("parent_key", "Client_Id"))
    assert not path.check(_Path("parent_key", "CLIENT_ID"))
    assert not path.check(_Path("parent_key", "ClientId"))


@pytest.mark.parametrize("factory", [_legpath, _netpath, _Path])
def test_path_factories_preserve_literal_asterisk_segments(factory):
    path = factory("Connections", "*")

    assert path.is_simple
    assert isinstance(path[-1], _SimplePathSegment)
    assert path[-1].check("*")
    assert not path[-1].check("Service")
    assert not path[-1].check(0)


@pytest.mark.parametrize("factory", [_Path, _get_segments, _legpath, _netpath])
def test_path_accepts_explicit_wildcard_segments(factory):
    marker = wildcard()
    path = _Path(*factory("Connections", marker))

    assert not path.is_simple
    assert path[-1] is marker
    assert path[-1].check("Service")
    assert path[-1].check(0)


@pytest.mark.parametrize("value", [None, False, 0, "", {}, []])
def test_missing_detection_does_not_confuse_present_falsy_values(value):
    assert _is_missing(_MISSING)
    assert _is_missing(_MissingType())
    assert not _is_missing(value)


@pytest.mark.parametrize("digit", ["\u00b2", "\u2081", "\u2460"])
def test_nondecimal_digit_segments_match_literal_keys_without_integer_conversion(digit):
    segment = _SimplePathSegment(digit)

    assert segment.check(digit)
    assert not segment.check(1)
    assert not segment.check("1")


@pytest.mark.parametrize("digit", ["01", "\u0661", "\uff11"])
def test_noncanonical_decimal_spellings_match_only_their_literal_key(digit):
    segment = _SimplePathSegment(digit)

    assert segment.check(digit)
    assert not segment.check(1)
    assert not segment.check("1")
    assert not _SimplePathSegment("1").check(digit)


@pytest.mark.parametrize("segments", [("Section", "Value"), ("0",)])
def test_path_create_accepts_tuple_sequences_declared_by_path_proxy(segments):
    path = _Path.create(segments)

    assert path.check(_Path.create(list(segments)))
    assert len(path) == len(segments)


def test_path_reverse_slice_preserves_each_segment_policy():
    path = _Path(
        _SimplePathSegment("Client_Id", ignore_case=True, ignore_underscores=True),
        _SimplePathSegment("Value"),
        _Wildcard(),
    )

    reversed_path = path[::-1]

    assert isinstance(reversed_path[0], _Wildcard)
    assert reversed_path[1] is path[1]
    assert reversed_path[2] is path[0]
    assert reversed_path.check(_Path("Anything", "Value", "CLIENTID"))
    assert not reversed_path.check(_Path("Anything", "value", "CLIENTID"))
    assert list(path[1:1]) == []


def test_segment_construction_rejects_empty_strings():
    with pytest.raises(ValueError, match="[Ee]mpty"):
        _SimplePathSegment("")


@pytest.mark.parametrize("segments", [[""], ["", ""], ["A", "", "B"]])
def test_path_constructor_rejects_empty_segments_without_silently_dropping_them(
    segments,
):
    with pytest.raises(ValueError, match="[Ee]mpty"):
        _Path.create(segments)
