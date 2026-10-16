# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import importlib.util
from pathlib import Path

import pytest

from microsoft_agents.copilotstudio.client import PowerPlatformCloud


@pytest.fixture
def sample(monkeypatch):
    sample_path = (
        Path(__file__).resolve().parents[2]
        / "test_samples"
        / "copilot_studio_client_sample"
    )
    monkeypatch.syspath_prepend(str(sample_path))
    spec = importlib.util.spec_from_file_location(
        "copilot_studio_console_sample", sample_path / "app.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("cloud", [PowerPlatformCloud.TEST, PowerPlatformCloud.PROD])
@pytest.mark.parametrize(
    "cached",
    [None, {"error": "interaction_required"}, {"access_token": "cached-token"}],
)
def test_sample_uses_configured_scope_and_interactive_fallback(
    sample, mocker, cloud, cached
):
    settings = sample.McsConnectionSettings(
        app_client_id="client",
        tenant_id="tenant",
        environment_id="environment",
        agent_identifier="agent",
        cloud=cloud,
    )
    mocker.patch.object(sample, "get_msal_token_cache")
    application = mocker.patch.object(sample, "PublicClientApplication").return_value
    application.get_accounts.return_value = ["account"]
    application.acquire_token_silent.return_value = cached
    application.acquire_token_interactive.return_value = {"access_token": "new-token"}

    token = sample.acquire_token(settings, "unused-cache")

    scope = (
        "https://api.test.powerplatform.com/.default"
        if cloud == PowerPlatformCloud.TEST
        else "https://api.powerplatform.com/.default"
    )
    application.acquire_token_silent.assert_called_once_with(
        scopes=[scope], account="account"
    )
    if cached and "access_token" in cached:
        assert token == "cached-token"
        application.acquire_token_interactive.assert_not_called()
    else:
        assert token == "new-token"
        application.acquire_token_interactive.assert_called_once_with(scopes=[scope])


def test_sample_signs_in_interactively_without_cached_accounts(sample, mocker):
    settings = sample.McsConnectionSettings(
        app_client_id="client",
        tenant_id="tenant",
        environment_id="environment",
        agent_identifier="agent",
        cloud=PowerPlatformCloud.TEST,
    )
    mocker.patch.object(sample, "get_msal_token_cache")
    application = mocker.patch.object(sample, "PublicClientApplication").return_value
    application.get_accounts.return_value = []
    application.acquire_token_interactive.return_value = {"access_token": "new-token"}
    assert sample.acquire_token(settings, "unused-cache") == "new-token"
    application.acquire_token_silent.assert_not_called()
    application.acquire_token_interactive.assert_called_once_with(
        scopes=["https://api.test.powerplatform.com/.default"]
    )
