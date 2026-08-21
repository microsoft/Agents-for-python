# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    Channels,
    TokenExchangeRequest,
)
from microsoft_agents.testing import MockUserTokenClient


@pytest.mark.asyncio
async def test_token_lifecycle_is_case_insensitive():
    client = MockUserTokenClient()
    client.add_user_token(
        connection_name="MyConnection",
        channel_id="MsTeams",
        user_id="User-1",
        token="secret-token",
    )

    token = await client.get_user_token(
        "user-1", "myconnection", "msteams", magic_code=None
    )
    statuses = await client.get_token_status("USER-1", "MSTEAMS")

    assert token.token == "secret-token"
    assert token.connection_name == "myconnection"
    assert [status.connection_name for status in statuses] == ["MyConnection"]
    assert statuses[0].has_token is True

    await client.sign_out_user("USER-1", "MYCONNECTION", "MSTEAMS")

    assert (
        await client.get_user_token(
            "user-1", "myconnection", "msteams", magic_code=None
        )
    ).token is None
    assert await client.get_token_status("user-1", "msteams") == []


@pytest.mark.asyncio
async def test_magic_code_unlocks_a_token_for_subsequent_requests():
    client = MockUserTokenClient()
    client.add_user_token(
        connection_name="connection",
        channel_id="test",
        user_id="user",
        token="magic-token",
        magic_code="123456",
    )

    before_unlock = await client.get_user_token(
        "user", "connection", "test", magic_code="wrong"
    )
    unlocked = await client.get_user_token(
        "user", "connection", "test", magic_code="123456"
    )
    after_unlock = await client.get_user_token(
        "user", "connection", "test", magic_code=None
    )

    assert before_unlock.token is None
    assert unlocked.token == "magic-token"
    assert after_unlock.token == "magic-token"


@pytest.mark.asyncio
async def test_token_or_sign_in_resource_follows_authentication_state():
    client = MockUserTokenClient()
    activity = Activity(
        type=ActivityTypes.message,
        channel_id=Channels.ms_teams,
        from_property=ChannelAccount(id="user"),
        recipient=ChannelAccount(id="bot"),
    )

    signed_out = await client.get_token_or_sign_in_resource("connection", activity)

    assert signed_out.token_response is None
    assert signed_out.sign_in_resource is not None
    assert (
        signed_out.sign_in_resource.sign_in_link
        == "https://fake.com/oauthsignin/connection/msteams/bot"
    )
    assert (
        signed_out.sign_in_resource.token_exchange_resource.uri
        == "api://connection/resource"
    )
    assert (
        signed_out.sign_in_resource.token_post_resource.sas_url
        == "https://fake.com/oauthsignin/connection/token"
    )

    client.add_user_token(
        connection_name="connection",
        channel_id=Channels.ms_teams,
        user_id="user",
        token="authenticated-token",
    )
    signed_in = await client.get_token_or_sign_in_resource("connection", activity)

    assert signed_in.token_response.token == "authenticated-token"
    assert signed_in.sign_in_resource is None


@pytest.mark.asyncio
async def test_token_status_can_be_filtered_by_connection():
    client = MockUserTokenClient()
    for connection in ("calendar", "mail", "files"):
        client.add_user_token(
            connection_name=connection,
            channel_id="test",
            user_id="user",
            token=f"{connection}-token",
        )

    statuses = await client.get_token_status("user", "test", include="mail,calendar")

    assert {status.connection_name for status in statuses} == {"mail", "calendar"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exchange_request", "exchangeable_item"),
    [
        (TokenExchangeRequest(token="incoming-token"), "incoming-token"),
        (
            TokenExchangeRequest(uri="api://incoming-resource"),
            "api://incoming-resource",
        ),
    ],
)
async def test_exchange_token_accepts_a_registered_token_or_uri(
    exchange_request: TokenExchangeRequest, exchangeable_item: str
):
    client = MockUserTokenClient()
    client.add_exchangeable_token(
        connection_name="connection",
        channel_id="test",
        user_id="user",
        exchangeable_item=exchangeable_item,
        token="exchanged-token",
    )

    response = await client.exchange_token(
        "user", "connection", "test", exchange_request
    )

    assert response.token == "exchanged-token"
    assert response.connection_name == "connection"
    assert response.channel_id == "test"


@pytest.mark.asyncio
async def test_exchange_token_supports_missing_and_failed_exchange_scenarios():
    client = MockUserTokenClient()

    missing = await client.exchange_token(
        "user",
        "connection",
        "test",
        TokenExchangeRequest(token="not-registered"),
    )
    assert missing.token is None

    client.raise_on_exchange_request(
        connection_name="connection",
        channel_id="test",
        user_id="user",
        exchangeable_item="failing-token",
    )
    with pytest.raises(Exception, match="Simulated exception"):
        await client.exchange_token(
            "user",
            "connection",
            "test",
            TokenExchangeRequest(token="failing-token"),
        )

    with pytest.raises(ValueError, match="Either token or uri"):
        await client.exchange_token(
            "user", "connection", "test", TokenExchangeRequest()
        )


@pytest.mark.asyncio
async def test_sign_in_requests_require_a_user_but_tolerate_missing_channel_fields():
    client = MockUserTokenClient()

    with pytest.raises(ValueError, match="'from' property"):
        await client.get_token_or_sign_in_resource(
            "connection", Activity(type=ActivityTypes.message)
        )

    resource = await client.get_sign_in_resource(
        "connection",
        Activity(
            type=ActivityTypes.message,
            from_property=ChannelAccount(id="user"),
        ),
    )

    assert resource.sign_in_link.endswith("/connection/unknown/unknown")


@pytest.mark.asyncio
async def test_unsupported_nested_clients_and_aad_tokens_have_explicit_contracts():
    client = MockUserTokenClient()

    with pytest.raises(NotImplementedError):
        _ = client.agent_sign_in
    with pytest.raises(NotImplementedError):
        _ = client.user_token

    assert (
        await client.get_aad_tokens(
            "user", "connection", ["https://graph.microsoft.com"], "test"
        )
        == {}
    )
    assert await client.close() is None
