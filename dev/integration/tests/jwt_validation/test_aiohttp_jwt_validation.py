# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pathlib import Path

import pytest
from dotenv import dotenv_values
from aiohttp import web

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.aiohttp import (
    jwt_authorization_decorator,
    jwt_authorization_middleware,
)
from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration
from microsoft_agents.testing.core.utils import sdk_config_connection

from tests.utils.pytest import skip_if_no_var
from tests.utils.config import REAL_SERVICE_CONNECTION_ENV_VARS

from ._helpers import (
    acquire_real_service_connection_token,
    auth_config_with_invalid_audience,
)

_requires_real_service_connection = skip_if_no_var(
    *REAL_SERVICE_CONNECTION_ENV_VARS, load_root_env_file=True
)
_JWT_VALIDATION_DIR = Path(__file__).parent
_ANONYMOUS_AUTH_CONFIG = sdk_config_connection(
    load_configuration_from_env(
        dotenv_values(_JWT_VALIDATION_DIR / "jwt_anonymous.env")
    )
)
_REQUIRED_AUTH_CONFIG = sdk_config_connection(
    load_configuration_from_env(dotenv_values(_JWT_VALIDATION_DIR / "jwt_required.env"))
)


async def _claims_handler(request):
    identity = request["claims_identity"]
    return web.json_response(
        {
            "authenticated": identity.is_authenticated,
            "authentication_type": identity.authentication_type,
        }
    )


def _create_app(
    *, use_global_middleware: bool, auth_config: AgentAuthConfiguration
):
    middlewares = [jwt_authorization_middleware] if use_global_middleware else []
    app = web.Application(middlewares=middlewares)
    app.agent_configuration = auth_config
    handler = (
        _claims_handler
        if use_global_middleware
        else jwt_authorization_decorator(_claims_handler)
    )
    app.router.add_get("/", handler)
    return app


@pytest.mark.asyncio
async def test_aiohttp_global_middleware_allows_anonymous_request_from_env_config(
    aiohttp_client,
):
    app = _create_app(use_global_middleware=True, auth_config=_ANONYMOUS_AUTH_CONFIG)
    client = await aiohttp_client(app)

    response = await client.get("/")

    assert response.status == 200
    assert await response.json() == {
        "authenticated": False,
        "authentication_type": "Anonymous",
    }


@pytest.mark.asyncio
async def test_aiohttp_global_middleware_rejects_invalid_bearer_token(aiohttp_client):
    app = _create_app(use_global_middleware=True, auth_config=_REQUIRED_AUTH_CONFIG)
    client = await aiohttp_client(app)

    response = await client.get("/", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status == 401
    assert await response.json() == {
        "error": "Invalid token or authentication failed."
    }


@_requires_real_service_connection
@pytest.mark.asyncio
async def test_aiohttp_global_middleware_accepts_real_service_connection_token(
    aiohttp_client,
):
    token, auth_config = await acquire_real_service_connection_token()
    app = web.Application(middlewares=[jwt_authorization_middleware])
    app.agent_configuration = auth_config
    app.router.add_get("/", _claims_handler)
    client = await aiohttp_client(app)

    response = await client.get("/", headers={"Authorization": f"Bearer {token}"})

    assert response.status == 200
    assert (await response.json())["authenticated"] is True


@_requires_real_service_connection
@pytest.mark.asyncio
async def test_aiohttp_global_middleware_rejects_real_token_with_invalid_audience(
    aiohttp_client,
):
    token, auth_config = await acquire_real_service_connection_token()
    app = web.Application(middlewares=[jwt_authorization_middleware])
    app.agent_configuration = auth_config_with_invalid_audience(auth_config)
    app.router.add_get("/", _claims_handler)
    client = await aiohttp_client(app)

    response = await client.get("/", headers={"Authorization": f"Bearer {token}"})

    assert response.status == 401
    assert await response.json() == {
        "error": "Invalid token or authentication failed."
    }


@pytest.mark.asyncio
async def test_aiohttp_decorator_allows_anonymous_request_from_env_config(
    aiohttp_client,
):
    app = _create_app(use_global_middleware=False, auth_config=_ANONYMOUS_AUTH_CONFIG)
    client = await aiohttp_client(app)

    response = await client.get("/")

    assert response.status == 200
    assert await response.json() == {
        "authenticated": False,
        "authentication_type": "Anonymous",
    }


@pytest.mark.asyncio
async def test_aiohttp_decorator_rejects_invalid_bearer_token(aiohttp_client):
    app = _create_app(use_global_middleware=False, auth_config=_REQUIRED_AUTH_CONFIG)
    client = await aiohttp_client(app)

    response = await client.get("/", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status == 401
    assert await response.json() == {
        "error": "Invalid token or authentication failed."
    }
