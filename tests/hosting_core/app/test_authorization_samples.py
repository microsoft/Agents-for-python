# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import importlib.util
import os
import sys
from pathlib import Path

import pytest

from microsoft_agents.activity import Activity, Attachment, TokenResponse
from microsoft_agents.hosting.core import TurnState


@pytest.fixture(params=["app_style", "fastapi"])
def sample(request, monkeypatch, mocker):
    sample_path = (
        Path(__file__).resolve().parents[3].joinpath("test_samples", request.param)
    )
    env = {
        f"AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{name}__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME": name.lower()
        for name in ("GRAPH", "GITHUB", "MCS")
    }
    env.update(
        {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "sample-client",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "sample-tenant",
        }
    )
    mocker.patch.dict(os.environ, env, clear=True)
    mocker.patch("dotenv.load_dotenv", return_value=False)
    for name in list(sys.modules):
        if name == "shared" or name.startswith("shared."):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.syspath_prepend(str(sample_path))
    spec = importlib.util.spec_from_file_location(
        f"_authorization_sample_{request.param}",
        sample_path / "authorization_agent.py",
    )
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        for name in list(sys.modules):
            if name == "shared" or name.startswith("shared."):
                del sys.modules[name]


@pytest.fixture
def context(mocker):
    context = mocker.Mock()
    context.send_activity = mocker.AsyncMock()
    return context


def test_samples_bind_environment_auth_handlers(sample):
    for handler_id in ("GRAPH", "GITHUB", "MCS"):
        handler = sample.AUTHORIZATION._resolve_handler(handler_id)

        assert handler._handler.abs_oauth_connection_name == handler_id.lower()


@pytest.mark.asyncio
async def test_status_handles_missing_tokens(sample, context, mocker):
    get_token = mocker.patch.object(
        sample.AUTHORIZATION,
        "get_token",
        side_effect=[TokenResponse(token="token"), None, TokenResponse()],
    )

    await sample.status(context, TurnState())

    assert get_token.await_args_list == [
        mocker.call(context, "GRAPH"),
        mocker.call(context, "GITHUB"),
        mocker.call(context, "MCS"),
    ]
    text = context.send_activity.await_args.args[0].text
    assert "GRAPH: Connected" in text
    assert "GITHUB: Not connected" in text
    assert "MCS: Not connected" in text


@pytest.mark.asyncio
async def test_logout_signs_out_of_all_services(sample, context, mocker):
    sign_out = mocker.patch.object(sample.AUTHORIZATION, "sign_out")
    handler = sample.sign_out if hasattr(sample, "sign_out") else sample.logout

    await handler(context, TurnState())

    assert sign_out.await_args_list == [
        mocker.call(context, "GRAPH"),
        mocker.call(context, "GITHUB"),
        mocker.call(context, "MCS"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("command, handler_id", [("login", "GRAPH"), ("prs", "GITHUB")])
async def test_protected_routes_wait_for_sign_in(
    sample, context, mocker, command, handler_id
):
    prefix = "/" if sample.__name__.endswith("fastapi") else ""
    context.activity = Activity(type="message", text=prefix + command)
    response = mocker.Mock()
    response.sign_in_complete.return_value = False
    sign_in = mocker.patch.object(
        sample.AUTHORIZATION, "_start_or_continue_sign_in", return_value=response
    )
    state = TurnState()

    await sample.AGENT_APP._on_activity(context, state)

    sign_in.assert_awaited_once_with(context, state, handler_id)
    context.send_activity.assert_not_awaited()


@pytest.mark.asyncio
async def test_login_requires_both_services(sample, context, mocker):
    command = "/login" if sample.__name__.endswith("fastapi") else "login"
    context.activity = Activity(type="message", text=command)
    response = mocker.Mock()
    response.sign_in_complete.return_value = True
    sign_in = mocker.patch.object(
        sample.AUTHORIZATION, "_start_or_continue_sign_in", return_value=response
    )
    state = TurnState()

    await sample.AGENT_APP._on_activity(context, state)

    assert sign_in.await_args_list == [
        mocker.call(context, state, "GRAPH"),
        mocker.call(context, state, "GITHUB"),
    ]
    context.send_activity.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("response", [None, TokenResponse()])
async def test_profile_does_not_call_graph_without_token(
    sample, context, mocker, response
):
    if hasattr(sample, "GraphClient"):
        graph = mocker.patch.object(sample.GraphClient, "get_me")
        mocker.patch.object(
            sample.AUTHORIZATION, "exchange_token", return_value=response
        )
    else:
        graph = mocker.patch.object(sample, "get_user_info")
        mocker.patch.object(sample.AUTHORIZATION, "get_token", return_value=response)

    await sample.profile_request(context, TurnState())

    graph.assert_not_awaited()
    context.send_activity.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("sample", ["app_style"], indirect=True)
async def test_github_profile_returns_when_token_is_missing(sample, context, mocker):
    mocker.patch.object(sample.AUTHORIZATION, "get_token", return_value=TokenResponse())
    get_profile = mocker.patch.object(sample.GitHubClient, "get_current_profile")

    await sample.profile_github(context, TurnState())

    get_profile.assert_not_awaited()
    context.send_activity.assert_awaited_once()


@pytest.mark.asyncio
async def test_pull_requests_does_not_call_github_without_token(
    sample, context, mocker
):
    mocker.patch.object(sample.AUTHORIZATION, "get_token", return_value=TokenResponse())
    target = sample.GitHubClient if hasattr(sample, "GitHubClient") else sample
    profile = mocker.patch.object(target, "get_current_profile")
    get_prs = mocker.patch.object(target, "get_pull_requests")

    await sample.pull_requests(context, TurnState())

    profile.assert_not_awaited()
    get_prs.assert_not_awaited()
    context.send_activity.assert_awaited_once()


@pytest.mark.asyncio
async def test_pull_requests_uses_github_client(sample, context, mocker):
    get_token = mocker.patch.object(
        sample.AUTHORIZATION, "get_token", return_value=TokenResponse(token="token")
    )
    target = sample.GitHubClient if hasattr(sample, "GitHubClient") else sample
    mocker.patch.object(target, "get_current_profile", return_value={})
    if target is sample:
        mocker.patch.object(
            sample,
            "create_profile_card",
            return_value=Attachment(
                content_type="application/vnd.microsoft.card.adaptive", content={}
            ),
        )
    get_prs = mocker.patch.object(target, "get_pull_requests", return_value=[])

    await sample.pull_requests(context, TurnState())

    get_token.assert_awaited_once_with(context, "GITHUB")
    get_prs.assert_awaited_once_with("octocat", "Hello-World", "token")
