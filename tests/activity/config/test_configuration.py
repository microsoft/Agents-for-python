# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import traceback
from collections.abc import MutableMapping

import pytest

from microsoft_agents.activity.config import Configuration, _legpath
from tests._common import create_configuration
from microsoft_agents.activity.config._metadata import _RootConfigMetadata


@pytest.mark.parametrize(
    "value, expected",
    [
        ("scope1 scope2", ["scope1", "scope2"]),
        ("scope1, scope2", ["scope1", "scope2"]),
        ("scope1,scope2 scope3", ["scope1", "scope2", "scope3"]),
        (" , \t ", []),
        (None, []),
    ],
)
def test_scope_strings_use_shared_whitespace_and_comma_normalization(value, expected):
    config = Configuration(dict(scopes=value))

    assert config.get_scopes("scopes") == expected


def test_section_uses_matched_alias_and_nested_path():
    config = create_configuration(
        {"Connections": {"Service": {"SETTINGS": {"Enabled": True}}}}, is_root=True
    )

    connection = config.get_section(_legpath("connections"))
    settings = connection.get_section(_legpath("Service", "settings"))

    assert connection._base_path == "Connections"
    assert settings._base_path == "Connections::Service::SETTINGS"
    assert _RootConfigMetadata.get(connection) is False
    assert _RootConfigMetadata.get(settings) is False
    assert settings.get_bool("Enabled") is True


def test_existing_configuration_section_is_rebased_without_modifying_original():
    original = Configuration({"Enabled": True}, _base_path="Previous")
    config = Configuration({"Settings": original}, _base_path="Service")

    section = config.get_section("Settings")

    assert section == original
    assert section is not original
    assert section._base_path == "Service::Settings"
    assert original._base_path == "Previous"


@pytest.mark.parametrize("is_root", [False, True])
def test_from_config_copies_outer_mapping_and_preserves_metadata(is_root):
    original = create_configuration(
        {"Enabled": True}, is_root=is_root, _base_path="Service"
    )

    copy = Configuration.from_config(original)

    assert copy is not original
    assert copy == original
    assert copy.base_path == "Service"
    assert _RootConfigMetadata.get(copy) is is_root


@pytest.mark.parametrize("is_root", [False, True])
@pytest.mark.parametrize("values", [{}, {"Enabled": True}])
def test_constructor_preserves_root_identity_when_copying_configuration(
    is_root, values
):
    original = create_configuration(values, is_root=is_root)

    copy = Configuration(original)

    assert copy is not original
    assert copy == original
    assert _RootConfigMetadata.get(copy) is is_root


@pytest.mark.parametrize("factory", [Configuration, Configuration.from_config])
@pytest.mark.parametrize("is_root", [False, True])
def test_explicit_root_override_does_not_change_original(factory, is_root):
    original = create_configuration({"Enabled": True}, is_root=is_root)

    copy = factory(original)
    _RootConfigMetadata.set(copy, not is_root)

    assert copy is not original
    assert copy["Enabled"] == original["Enabled"]
    assert _RootConfigMetadata.get(copy) is not is_root
    assert _RootConfigMetadata.get(original) is is_root


def test_empty_base_path_inherits_original_diagnostic_path():
    original = Configuration({"Enabled": True}, _base_path="Service")

    rebased = Configuration.from_config(original, _base_path="")

    assert rebased._base_path == "Service"
    assert original._base_path == "Service"


def test_missing_section_preserves_default_configuration_identity():
    config = Configuration(_base_path="Service")
    default = Configuration({"Enabled": True}, _base_path="Fallback")

    assert config.get_section("Missing", default=default) is default
    assert default._base_path == "Fallback"
    assert config.get_section("Missing", default=None) is None


@pytest.mark.parametrize("getter", ["get_section", "get_int"])
def test_missing_required_value_reports_full_path(getter):
    config = Configuration({"Settings": {}}).get_section("Settings")

    with pytest.raises(KeyError) as error:
        getattr(config, getter)("Missing")

    assert error.value.args == ("Settings::Missing",)


def test_non_mapping_section_reports_matched_alias_without_its_value():
    config = Configuration({"Settings": {"TOKEN": "synthetic-secret"}})
    settings = config.get_section("Settings")

    with pytest.raises(TypeError) as error:
        settings.get_section(_legpath("token"))

    assert str(error.value) == "Section Settings::TOKEN is not a mapping"


@pytest.mark.parametrize(
    "getter, value, expected_path",
    [
        ("get_bool", "synthetic-secret", "Settings::VALUE"),
        ("get_int", "synthetic-secret", "Settings::VALUE"),
        ("get_float", "synthetic-secret", "Settings::VALUE"),
        ("get_str_list", {"token": "synthetic-secret"}, "Settings::VALUE"),
        ("get_scopes", {"token": "synthetic-secret"}, "Settings::value"),
    ],
)
def test_conversion_errors_report_full_path_without_input(getter, value, expected_path):
    config = Configuration({"Settings": {"VALUE": value}})
    settings = config.get_section("Settings")

    with pytest.raises(ValueError) as error:
        getattr(settings, getter)(_legpath("value"))

    assert expected_path in str(error.value)
    assert "synthetic-secret" not in "".join(
        traceback.format_exception_only(type(error.value), error.value)
    )
    assert error.value.__cause__ is None
    if error.value.__context__ is not None:
        assert error.value.__suppress_context__


@pytest.mark.parametrize(
    "getter, value, expected",
    [
        ("get_bool", "false", False),
        ("get_int", "42", 42),
        ("get_float", "1.5", 1.5),
        ("get_str", 42, "42"),
        ("get_str_list", ["read", "write"], ["read", "write"]),
        ("get_scopes", "read write", ["read", "write"]),
    ],
)
def test_diagnostic_paths_preserve_successful_conversion(getter, value, expected):
    settings = Configuration({"Settings": {"VALUE": value}}).get_section("Settings")

    assert getattr(settings, getter)(_legpath("value")) == expected


@pytest.mark.parametrize(
    "getter, default",
    [
        ("get_bool", False),
        ("get_int", 5),
        ("get_float", 1.5),
        ("get_str", "fallback"),
        ("get_str_list", ["fallback"]),
    ],
)
def test_conversion_preserves_missing_defaults(getter, default):
    settings = Configuration(_base_path="Settings")

    assert getattr(settings, getter)("Missing", default=default) == default


@pytest.mark.parametrize(
    "value, expected",
    [
        (["read", "write"], ["read", "write"]),
        ("read write", ["read", "write"]),
        (" read\twrite\n", ["read", "write"]),
        ("read,write", ["read", "write"]),
        (" read, write ", ["read", "write"]),
        ("", []),
        ("  ", []),
        (None, []),
    ],
)
def test_string_lists_bind_supported_formats(value, expected):
    config = Configuration({"VALUES": value})

    assert config.get_str_list("VALUES") == expected


def test_string_list_rejects_unresolved_indexed_mapping_even_with_default():
    config = Configuration({"VALUES": {"0": "read"}}, _base_path="Settings")

    with pytest.raises(ValueError, match="Settings::VALUES"):
        config.get_str_list("VALUES", default=["fallback"])


@pytest.mark.parametrize("getter", ["get_bool", "get_booln"])
@pytest.mark.parametrize("default", [True, False, None])
@pytest.mark.parametrize("value", ["yes", "on", "no", "off", "maybe"])
def test_boolean_getters_reject_unrecognized_values_with_defaults(
    getter, default, value
):
    settings = Configuration({"Enabled": value}, _base_path="Settings")

    with pytest.raises(ValueError, match="Invalid boolean for Settings::Enabled"):
        getattr(settings, getter)("Enabled", default=default)


def test_skipped_null_value_has_no_matched_path():
    config = Configuration({"Settings": {"VALUE": None}})
    settings = config.get_section("Settings")

    value, matched_path = settings._get_with_path(
        _legpath("value"), default=None, skip_none=True
    )

    assert value is None
    assert matched_path is None
    assert settings.get_int(_legpath("value"), default=5) == 5

    value, matched_path = settings._get_with_path(_legpath("value"))
    assert value is None
    assert str(matched_path) == "VALUE"


def test_collected_sections_rebase_existing_configurations():
    original = Configuration({"Enabled": True}, _base_path="Previous")
    config = Configuration({"Entries": {"Service": original}}, _base_path="Root")

    sections = config.get_sections(_legpath("Entries", "*"))

    assert len(sections) == 1
    assert sections[0]._base_path == "Root::Entries::Service"
    assert original._base_path == "Previous"


def test_non_mapping_collected_section_reports_full_path():
    config = Configuration(
        {"Entries": {"Service": "synthetic-secret"}}, _base_path="Root"
    )

    with pytest.raises(TypeError) as error:
        config.get_sections(_legpath("Entries", "*"))

    assert str(error.value) == "Section Root::Entries::Service is not a mapping"


def test_configuration_is_a_mutable_mapping_with_positional_default_lookup():
    config = Configuration({"Enabled": False, "Optional": None})
    fallback = object()

    assert isinstance(config, MutableMapping)
    assert config.get("Enabled", fallback) is False
    assert config.get("Optional", fallback) is None
    assert config.get("Missing", fallback) is fallback
    assert config.get(["Missing", "Enabled"], fallback) is fallback


@pytest.mark.parametrize("is_root", [False, True])
def test_resolve_merges_defaults_without_mutating_inputs(is_root):
    primary = create_configuration({"settings": {"enabled": False}}, is_root=is_root)
    defaults = {"settings": {"enabled": True, "count": 3}}
    original = dict(primary)

    config = Configuration._resolve(primary, defaults)
    config["settings"]["count"] = 4

    assert config.get_bool(["settings", "enabled"]) is False
    assert _RootConfigMetadata.get(config) is True
    assert primary == original
    assert defaults == {"settings": {"enabled": True, "count": 3}}


def test_resolve_can_leave_unmarked_configuration_scoped():
    config = Configuration._resolve({"enabled": True}, _ensure_root_config=False)

    assert _RootConfigMetadata.get(config) is False


@pytest.mark.parametrize("is_root", [False, True])
def test_from_config_forks_top_level_values_and_preserves_base_path(is_root):
    original = create_configuration(
        {"Enabled": False}, is_root=is_root, _base_path="Service"
    )

    fork = Configuration.from_config(original)
    fork["Enabled"] = True
    fork["Count"] = 3

    assert fork is not original
    assert fork._base_path == "Service"
    assert _RootConfigMetadata.get(fork) is is_root
    assert fork["Enabled"] is True
    assert fork["Count"] == 3
    assert original["Enabled"] is False
    assert "Count" not in original


def test_from_config_preserves_literal_key_spelling():
    original = Configuration({"Enabled": False})

    assert Configuration.from_config(original)["Enabled"] is False
    assert "enabled" not in Configuration.from_config(original)


def test_constructor_wraps_plain_nested_containers_without_sharing_them():
    source = {"Values": ["original"]}
    config = Configuration(source)

    source["New"] = True
    source["Values"].append("shared")

    assert "New" not in config
    assert config["Values"] == ["original"]


@pytest.mark.parametrize(
    "entries",
    [
        [("client_id", "lower"), ("CLIENT_ID", "upper"), ("CLIENTID", "compact")],
        [("CLIENTID", "compact"), ("CLIENT_ID", "upper"), ("client_id", "lower")],
    ],
)
def test_matching_aliases_follow_source_insertion_order(entries):
    assert Configuration(dict(entries)).get_str(_legpath("client_id")) == entries[0][1]


def test_legacy_matching_components_form_one_nested_path():
    config = Configuration(
        {"AGENTAPPLICATION": {"USERAUTHORIZATION": {"Enabled": True}}}
    )

    section = config.get_section(_legpath("agent_application", "user_authorization"))

    assert section.get_bool("Enabled") is True
    assert section._base_path == "AGENTAPPLICATION::USERAUTHORIZATION"


@pytest.mark.parametrize(
    "values, index, expected",
    [
        (["first", "second"], 0, []),
        ({"0": "first", "1": "second"}, "0", ["first", "second"]),
    ],
)
def test_collect_wildcards_enumerate_mappings_not_lists(values, index, expected):
    config = Configuration({"audiences": values})

    assert config.collect_str(_legpath("audiences", "*")) == expected
    assert config.collect_str(["audiences", index]) == ["first"]


def test_collect_does_not_implicitly_flatten_selected_containers():
    values = ["first", "second"]
    config = Configuration({"audiences": values})

    assert config.collect("audiences") == [values]
    assert config.collect_str("audiences") == [str(values)]
    assert config.collect_str(["audiences", 0]) == ["first"]


def test_collect_preserves_equal_values_under_distinct_source_keys():
    config = Configuration({"Values": {"First": "same", "Second": "same"}})

    assert config.collect_str(_legpath("Values", "*")) == ["same", "same"]


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, []),
        ("", []),
        ("  ", []),
        ([], []),
        ("read\twrite\n", ["read", "write"]),
        (["read", "write"], ["read", "write"]),
    ],
)
def test_scopes_bind_supported_list_and_whitespace_formats(value, expected):
    config = Configuration({"SCOPES": value})

    assert config.get_scopes("SCOPES") == expected
