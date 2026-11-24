# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import Mock

import pytest

from microsoft_agents.activity.config import load_configuration_from_env
from microsoft_agents.hosting.core import MemoryStorage
from microsoft_agents.hosting.core.app import (
    AgentApplication,
    ApplicationOptions,
    InputFileDownloader,
    TurnState,
)
from microsoft_agents.hosting.core.app.oauth import Authorization, AuthHandlerConfig
from microsoft_agents.hosting.core.app.proactive import ProactiveOptions
from microsoft_agents.hosting.core.app.typing_indicator import TypingOptions
from microsoft_agents.hosting.core.channel_service_adapter import ChannelServiceAdapter
from tests._common import create_configuration
from tests._common.testing_objects import TestingConnectionManager as _ConnectionManager


def _key(name, style):
    if style == "pascal":
        return "".join(part.capitalize() for part in name.split("_"))
    if style == "upper":
        return name.upper()
    return name


def _configuration(values, is_root):
    return create_configuration(
        {"AgentApplication": values} if is_root else values,
        is_root=is_root,
    )


@pytest.mark.parametrize("is_root", [False, True], ids=["scoped", "root"])
@pytest.mark.parametrize("style", ["snake", "pascal", "upper"])
def test_binds_scalar_settings_with_configuration_aliases(is_root, style):
    values = {
        "bot_app_id": "test-agent",
        "start_typing_timer": "false",
        "remove_recipient_mention": "0",
        "long_running_messages": "true",
    }
    config = _configuration(
        {_key(name, style): value for name, value in values.items()}, is_root
    )

    options = ApplicationOptions.from_config(config)

    assert options.bot_app_id == "test-agent"
    assert options.start_typing_timer is False
    assert options.remove_recipient_mention is False
    assert options.long_running_messages is True


@pytest.fixture
def runtime_dependencies():
    return {
        "storage": MemoryStorage(),
        "typing": TypingOptions(initial_delay_ms=100, interval_ms=2000),
        "proactive": ProactiveOptions(fail_on_unsigned_in_connections=False),
        "turn_state_factory": TurnState,
        "file_downloaders": [Mock(spec=InputFileDownloader)],
        "adapter": Mock(spec=ChannelServiceAdapter),
        "authorization_handlers": {"graph": AuthHandlerConfig(name="graph")},
    }


@pytest.mark.parametrize("is_root", [False, True], ids=["scoped", "root"])
def test_preserves_runtime_dependencies(runtime_dependencies, is_root):
    config = _configuration(runtime_dependencies, is_root)

    options = ApplicationOptions.from_config(config)

    for name in ("storage", "typing", "proactive", "turn_state_factory", "adapter"):
        assert getattr(options, name) is runtime_dependencies[name], name
    assert options.file_downloaders[0] is runtime_dependencies["file_downloaders"][0]
    assert (
        options.authorization_handlers["graph"]
        is runtime_dependencies["authorization_handlers"]["graph"]
    )


@pytest.mark.parametrize(
    "name, value, message",
    [
        ("storage", object(), "storage must be an instance of Storage"),
        ("typing", {}, "typing must be an instance of TypingOptions"),
        ("proactive", {}, "proactive must be an instance of ProactiveOptions"),
        ("adapter", object(), "adapter must be an instance of ChannelServiceAdapter"),
        ("authorization_handlers", [], "authorization_handlers must be a mapping"),
        ("file_downloaders", object(), "file_downloaders must be a list"),
        ("file_downloaders", [object()], "each item in file_downloaders"),
    ],
)
def test_rejects_invalid_runtime_dependencies(name, value, message):
    with pytest.raises(TypeError, match=message):
        ApplicationOptions.from_config({name: value})


def test_invalid_scalar_reports_root_configuration_path_without_value():
    config = _configuration({"StartTypingTimer": "invalid-setting-value"}, True)

    with pytest.raises(ValueError, match="AgentApplication::StartTypingTimer") as error:
        ApplicationOptions.from_config(config)

    assert "invalid-setting-value" not in str(error.value)


@pytest.mark.parametrize("bind_options", [False, True], ids=["legacy-kwargs", "bound"])
def test_application_preserves_legacy_scope_and_forwards_authorization(bind_options):
    config = load_configuration_from_env(
        {
            "AGENTAPPLICATION__STARTTYPINGTIMER": "false",
            "AGENTAPPLICATION__REMOVERECIPIENTMENTION": "false",
            "AGENTAPPLICATION__USERAUTHORIZATION__AUTO_SIGN_IN": "true",
        }
    )
    original_config = dict(config)
    storage = MemoryStorage()
    kwargs = (
        {"options": ApplicationOptions.from_config(config), "config": config}
        if bind_options
        else dict(config)
    )

    app = AgentApplication(
        storage=storage,
        connection_manager=_ConnectionManager(),
        **kwargs,
    )

    assert app.options.start_typing_timer is not bind_options
    assert app.options.remove_recipient_mention is not bind_options
    assert app.options.storage is storage
    assert app.auth._auto_sign_in is True
    assert isinstance(app._turn_state_factory(), TurnState)
    assert config == original_config


@pytest.mark.parametrize(
    "kwargs, error_type, message",
    [
        (
            {"start_typing_timer": "invalid-setting"},
            ValueError,
            "Invalid boolean for start_typing_timer",
        ),
        (
            {"typing": {"invalid": True}},
            TypeError,
            "typing must be an instance of TypingOptions",
        ),
    ],
)
def test_explicit_options_still_validate_kwargs(kwargs, error_type, message):
    storage = MemoryStorage()

    with pytest.raises(error_type, match=message):
        AgentApplication(
            options=ApplicationOptions(storage=storage, start_typing_timer=False),
            authorization=Authorization(storage, _ConnectionManager()),
            **kwargs,
        )


def test_explicit_options_override_valid_kwargs():
    storage = MemoryStorage()
    app = AgentApplication(
        options=ApplicationOptions(storage=storage, start_typing_timer=False),
        authorization=Authorization(storage, _ConnectionManager()),
        storage=MemoryStorage(),
        start_typing_timer=True,
    )

    assert app.options.storage is storage
    assert app.options.start_typing_timer is False


@pytest.mark.parametrize("has_explicit_downloaders", [False, True])
def test_downloaders_use_kwargs_when_explicit_options_are_empty(
    has_explicit_downloaders,
):
    storage = MemoryStorage()
    explicit_downloaders = (
        [Mock(spec=InputFileDownloader)] if has_explicit_downloaders else []
    )
    fallback_downloader = Mock(spec=InputFileDownloader)
    app = AgentApplication(
        options=ApplicationOptions(
            storage=storage, file_downloaders=explicit_downloaders
        ),
        authorization=Authorization(storage, _ConnectionManager()),
        file_downloaders=[fallback_downloader],
    )

    expected = (
        explicit_downloaders[0] if has_explicit_downloaders else fallback_downloader
    )
    assert len(app.options.file_downloaders) == 1
    assert app.options.file_downloaders[0] is expected
