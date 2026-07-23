# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pathlib import Path

import pytest
from dotenv import dotenv_values
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration
from microsoft_agents.hosting.fastapi import (
    JwtAuthorizationMiddleware,
    jwt_authorization_decorator,
)
from microsoft_agents.testing.core.utils import sdk_config_connection

from tests.utils.config import REAL_SERVICE_CONNECTION_ENV_VARS
from tests.utils.pytest import skip_if_no_var

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


def _claims_payload(request: Request):
    identity = request.state.claims_identity
    return {
        "authenticated": identity.is_authenticated,
        "authentication_type": identity.authentication_type,
    }


def _create_app(
    *, use_global_middleware: bool, auth_config: AgentAuthConfiguration
):
    app = FastAPI()
    app.state.agent_configuration = auth_config

    if use_global_middleware:
        app.add_middleware(JwtAuthorizationMiddleware)

        @app.get("/")
        async def handler(request: Request):
            return _claims_payload(request)

    else:

        @app.get("/")
        @jwt_authorization_decorator
        async def handler(request: Request):
            return _claims_payload(request)

    return app


def test_fastapi_global_middleware_allows_anonymous_request_from_env_config():
    client = TestClient(
        _create_app(use_global_middleware=True, auth_config=_ANONYMOUS_AUTH_CONFIG)
    )

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": False,
        "authentication_type": "Anonymous",
    }


def test_fastapi_global_middleware_rejects_invalid_bearer_token():
    client = TestClient(
        _create_app(use_global_middleware=True, auth_config=_REQUIRED_AUTH_CONFIG)
    )

    response = client.get("/", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid token or authentication failed."}


@_requires_real_service_connection
@pytest.mark.asyncio
async def test_fastapi_global_middleware_accepts_real_service_connection_token():
    token, auth_config = await acquire_real_service_connection_token()
    client = TestClient(
        _create_app(use_global_middleware=True, auth_config=auth_config)
    )

    response = client.get("/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["authenticated"] is True


@_requires_real_service_connection
@pytest.mark.asyncio
async def test_fastapi_global_middleware_rejects_real_token_with_invalid_audience():
    token, auth_config = await acquire_real_service_connection_token()
    client = TestClient(
        _create_app(
            use_global_middleware=True,
            auth_config=auth_config_with_invalid_audience(auth_config),
        )
    )

    response = client.get("/", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid token or authentication failed."}


def test_fastapi_decorator_allows_anonymous_request_from_env_config():
    client = TestClient(
        _create_app(use_global_middleware=False, auth_config=_ANONYMOUS_AUTH_CONFIG)
    )

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": False,
        "authentication_type": "Anonymous",
    }


def test_fastapi_decorator_rejects_invalid_bearer_token():
    client = TestClient(
        _create_app(use_global_middleware=False, auth_config=_REQUIRED_AUTH_CONFIG)
    )

    response = client.get("/", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid token or authentication failed."}
