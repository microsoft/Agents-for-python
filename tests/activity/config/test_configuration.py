# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import traceback

import pytest

from microsoft_agents.activity.config import Configuration, path, xpath


def test_section_uses_matched_alias_and_nested_path():
    config = Configuration(
        {"Connections": {"Service": {"SETTINGS": {"Enabled": True}}}}
    )

    connection = config.get_section(["CONNECTIONS", "Connections"])
    settings = connection.get_section(["Service::settings", "Service::SETTINGS"])

    assert connection._base_path == "Connections"
    assert settings._base_path == "Connections::Service::SETTINGS"
    assert settings.get_bool("Enabled") is True


def test_existing_configuration_section_is_rebased_without_modifying_original():
    original = Configuration({"Enabled": True}, _base_path="Previous")
    config = Configuration({"Settings": original}, _base_path="Service")

    section = config.get_section("Settings")

    assert section == original
    assert section is not original
    assert section._base_path == "Service::Settings"
    assert original._base_path == "Previous"


def test_from_mapping_reuses_configuration_when_base_path_is_unchanged():
    original = Configuration({"Enabled": True}, _base_path="Service")

    assert Configuration.from_mapping(original) is original
    assert Configuration.from_mapping(original, _base_path="Service") is original


def test_from_mapping_can_rebase_to_root():
    original = Configuration({"Enabled": True}, _base_path="Service")

    rebased = Configuration.from_mapping(original, _base_path="")

    assert rebased._base_path == ""
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
        settings.get_section("token", "TOKEN")

    assert str(error.value) == "Section Settings::TOKEN is not a mapping"


@pytest.mark.parametrize(
    "getter, value",
    [
        ("get_bool", "synthetic-secret"),
        ("get_int", "synthetic-secret"),
        ("get_float", "synthetic-secret"),
        ("get_str_list", "synthetic-secret"),
        ("get_scopes", {"token": "synthetic-secret"}),
    ],
)
def test_conversion_errors_report_matched_full_path_without_input(getter, value):
    config = Configuration({"Settings": {"VALUE": value}})
    settings = config.get_section("Settings")

    with pytest.raises(ValueError) as error:
        getattr(settings, getter)("value", "VALUE")

    assert "Settings::VALUE" in str(error.value)
    assert "Settings::value" not in str(error.value)
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

    assert getattr(settings, getter)("value", "VALUE") == expected


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


@pytest.mark.parametrize("getter", ["get_bool", "get_booln"])
@pytest.mark.parametrize("default", [True, False, None])
@pytest.mark.parametrize("value", ["yes", "on", "no", "off", "maybe"])
def test_boolean_getters_reject_unrecognized_values_with_defaults(
    getter, default, value
):
    settings = Configuration({"Enabled": value}, _base_path="Settings")

    with pytest.raises(ValueError, match="Invalid boolean for Settings::Enabled"):
        getattr(settings, getter)("Enabled", default=default)


def test_null_value_preserves_matched_path_when_skipped():
    config = Configuration({"Settings": {"VALUE": None}})
    settings = config.get_section("Settings")

    value, matched_path = settings._get_with_path(
        "value", "VALUE", default=None, skip_none=True
    )

    assert value is None
    assert matched_path == ["VALUE"]
    assert settings.get_int("value", "VALUE", default=5) == 5


def test_collected_sections_rebase_existing_configurations():
    original = Configuration({"Enabled": True}, _base_path="Previous")
    config = Configuration({"Entries": {"Service": original}}, _base_path="Root")

    sections = config.get_sections(path("Entries", "*"))

    assert len(sections) == 1
    assert sections[0]._base_path == "Root::Entries::Service"
    assert original._base_path == "Previous"


def test_non_mapping_collected_section_reports_full_path():
    config = Configuration(
        {"Entries": {"Service": "synthetic-secret"}}, _base_path="Root"
    )

    with pytest.raises(TypeError) as error:
        config.get_sections(path("Entries", "*"))

    assert str(error.value) == "Section Root::Entries::Service is not a mapping"


def test_configuration_is_a_dictionary_with_positional_default_lookup():
    config = Configuration({"Enabled": False, "Optional": None})
    fallback = object()

    assert isinstance(config, dict)
    assert config.get("Enabled", fallback) is False
    assert config.get("Optional", fallback) is None
    assert config.get("Missing", fallback) is fallback
    assert config.get(["Missing", "Enabled"], fallback) is False


def test_from_mapping_merges_defaults_without_mutating_inputs():
    primary = {"Settings": {"Enabled": False}}
    defaults = {"Settings": {"Enabled": True, "Count": 3}}

    config = Configuration.from_mapping(primary, **defaults)
    config["Settings"]["Count"] = 4

    assert config.get_bool("Settings::Enabled") is False
    assert primary == {"Settings": {"Enabled": False}}
    assert defaults == {"Settings": {"Enabled": True, "Count": 3}}


def test_from_config_forks_top_level_values_and_preserves_base_path():
    original = Configuration({"Enabled": False}, _base_path="Service")

    fork = Configuration.from_config(original, Enabled=True, Count=3)
    fork["Enabled"] = True

    assert fork is not original
    assert fork._base_path == "Service"
    assert fork["Count"] == 3
    assert original["Enabled"] is False
    assert "Count" not in original


def test_from_config_preserves_primary_values_over_fallbacks():
    original = Configuration({"Enabled": False})

    assert Configuration.from_config(original, Enabled=True)["Enabled"] is False


def test_constructor_makes_a_shallow_copy():
    source = {"Values": ["original"]}
    config = Configuration(source)

    source["New"] = True
    source["Values"].append("shared")

    assert "New" not in config
    assert config["Values"] == ["original", "shared"]


@pytest.mark.parametrize(
    "entries",
    [
        [("client_id", "lower"), ("CLIENT_ID", "upper"), ("CLIENTID", "compact")],
        [("CLIENTID", "compact"), ("CLIENT_ID", "upper"), ("client_id", "lower")],
    ],
)
def test_alias_precedence_does_not_depend_on_insertion_order(entries):
    assert Configuration(dict(entries)).get_str(xpath("client_id")) == "compact"


def test_xpath_components_form_one_nested_path():
    config = Configuration(
        {"AGENTAPPLICATION": {"USERAUTHORIZATION": {"Enabled": True}}}
    )

    section = config.get_section(xpath("agent_application", "user_authorization"))

    assert section.get_bool("Enabled") is True
    assert section._base_path == "AGENTAPPLICATION::USERAUTHORIZATION"


@pytest.mark.parametrize("values", [["first", "second"], {"0": "first", "1": "second"}])
def test_collect_str_selects_children_of_lists_and_indexed_mappings(values):
    config = Configuration({"audiences": values})

    assert config.collect_str("audiences::*") == ["first", "second"]


def test_collect_does_not_implicitly_flatten_selected_containers():
    values = ["first", "second"]
    config = Configuration({"audiences": values})

    assert config.collect("audiences") == [values]
    assert config.collect_str("audiences") == [str(values)]
    assert config.collect_str("audiences::*") == values


def test_collect_deduplicates_overlapping_paths_not_equal_values():
    config = Configuration({"Values": ["same", "same"]})

    assert config.collect_str("Values::*", "Values::0") == ["same", "same"]


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
