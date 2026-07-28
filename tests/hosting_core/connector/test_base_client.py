# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# pylint: disable=missing-class-docstring,missing-function-docstring,protected-access,too-few-public-methods

"""Tests for connector base client header propagation."""

from typing import cast

import pytest
from aiohttp import ClientSession

from microsoft_agents.hosting.core.connector.client._base_client import (
    _BaseClient,
    _ClientSessionWrapper,
)
from microsoft_agents.hosting.core.header_propagation import (
    HeaderPropagationContext,
    HeaderValueProvider,
)


class _HeaderProvider(HeaderValueProvider):
    def __init__(self, headers: dict[str, str]):
        self.headers = headers

    def get_headers(self) -> dict[str, str]:
        return dict(self.headers)


class _FakeSession:
    def __init__(self):
        self._base_url = "https://example.test/"
        self.marker = "fake-session"
        self.calls = []

    def get(self, *args, **kwargs):
        self.calls.append(("GET", args, kwargs))
        return "get-result"

    def post(self, *args, **kwargs):
        self.calls.append(("POST", args, kwargs))
        return "post-result"


@pytest.fixture(autouse=True)
def reset_header_propagation_context():
    HeaderPropagationContext.reset()
    yield
    HeaderPropagationContext.reset()


class TestClientSessionWrapper:
    def test_merges_propagated_headers_with_request_headers(self):
        fake_session = _FakeSession()
        wrapper = _ClientSessionWrapper(cast(ClientSession, fake_session))
        HeaderPropagationContext.register(
            _HeaderProvider(
                {
                    "X-Propagated": "propagated-value",
                    "X-Override": "propagated-value",
                }
            )
        )

        result = wrapper.get(
            "v3/conversations",
            headers={
                "X-Request": "request-value",
                "X-Override": "request-value",
            },
        )

        assert result == "get-result"
        _, args, kwargs = fake_session.calls[0]
        assert args == ("v3/conversations",)
        assert kwargs["headers"] == {
            "X-Request": "request-value",
            "X-Override": "request-value",
            "X-Propagated": "propagated-value",
        }

    def test_collects_headers_for_each_request(self):
        fake_session = _FakeSession()
        wrapper = _ClientSessionWrapper(cast(ClientSession, fake_session))
        provider = _HeaderProvider({"X-Turn": "first"})
        HeaderPropagationContext.register(provider)

        wrapper.get("first")
        provider.headers = {"X-Turn": "second"}
        wrapper.post("second")

        assert fake_session.calls[0][2]["headers"]["X-Turn"] == "first"
        assert fake_session.calls[1][2]["headers"]["X-Turn"] == "second"

    def test_delegates_unknown_attributes_to_wrapped_session(self):
        wrapper = _ClientSessionWrapper(cast(ClientSession, _FakeSession()))

        assert wrapper.marker == "fake-session"


class TestBaseClient:
    def test_wrapped_client_returns_header_propagating_wrapper(self):
        fake_session = _FakeSession()
        client = _BaseClient(cast(ClientSession, fake_session))
        HeaderPropagationContext.register(_HeaderProvider({"X-Propagated": "value"}))

        result = getattr(client, "_wrapped_client")().get("path")

        assert result == "get-result"
        assert fake_session.calls[0][2]["headers"] == {"X-Propagated": "value"}
