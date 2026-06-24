# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.task_modules (task/fetch and task/submit invokes)."""

import re
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_teams.api.models import TaskModuleRequest, TaskModuleResponse
    from microsoft_agents.hosting.msteams import TeamsAgentExtension

_PATCH = (
    "microsoft_agents.hosting.msteams.task_module.task_module._send_invoke_response"
)


class TestTaskModuleFetch:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    # ── Selector tests ──────────────────────────────────────────────────────

    def test_fetch_no_verb_matches_any(self):
        @self.ext.task_modules.fetch()
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        ctx = _make_context(ActivityTypes.invoke, name="task/fetch", value={})
        assert selector(ctx) is True

    def test_fetch_verb_matches_exact(self):
        @self.ext.task_modules.fetch("myVerb")
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="task/fetch",
                    value={"data": {"verb": "myVerb"}},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="task/fetch",
                    value={"data": {"verb": "otherVerb"}},
                )
            )
            is False
        )

    def test_fetch_verb_matches_regex(self):
        @self.ext.task_modules.fetch(re.compile(r"my.*"))
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="task/fetch",
                    value={"data": {"verb": "mySpecialVerb"}},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="task/fetch",
                    value={"data": {"verb": "otherVerb"}},
                )
            )
            is False
        )

    def test_fetch_wrong_invoke_name(self):
        @self.ext.task_modules.fetch()
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(_make_context(ActivityTypes.invoke, name="task/submit", value={}))
            is False
        )

    def test_fetch_wrong_activity_type(self):
        @self.ext.task_modules.fetch()
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(_make_context(ActivityTypes.message, name="task/fetch")) is False
        )

    def test_fetch_is_invoke(self):
        @self.ext.task_modules.fetch()
        async def handler(ctx, state, req): ...

        assert self.app._routes[0]["is_invoke"] is True

    # ── Handler tests ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_fetch_handler_passes_request_and_sends_response(self):
        response = TaskModuleResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.task_modules.fetch()
        async def handler(ctx, state, req: TaskModuleRequest):
            return await user_handler(ctx, state, req)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="task/fetch",
            value={"data": {"verb": "myVerb"}, "context": None},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert user_handler.called
            assert isinstance(user_handler.call_args[0][2], TaskModuleRequest)
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_fetch_handler_skips_send_when_none_returned(self):
        @self.ext.task_modules.fetch()
        async def handler(ctx, state, req): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="task/fetch",
            value={"data": None, "context": None},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            mock_send.assert_not_awaited()


class TestTaskModuleSubmit:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_submit_no_verb_matches_any(self):
        @self.ext.task_modules.submit()
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(_make_context(ActivityTypes.invoke, name="task/submit", value={}))
            is True
        )

    def test_submit_verb_matches_exact(self):
        @self.ext.task_modules.submit("submitVerb")
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="task/submit",
                    value={"data": {"verb": "submitVerb"}},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.invoke,
                    name="task/submit",
                    value={"data": {"verb": "other"}},
                )
            )
            is False
        )

    def test_submit_wrong_invoke_name(self):
        @self.ext.task_modules.submit()
        async def handler(ctx, state, req): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(_make_context(ActivityTypes.invoke, name="task/fetch", value={}))
            is False
        )

    def test_submit_is_invoke(self):
        @self.ext.task_modules.submit()
        async def handler(ctx, state, req): ...

        assert self.app._routes[0]["is_invoke"] is True

    @pytest.mark.asyncio
    async def test_submit_handler_passes_request_and_sends_response(self):
        response = TaskModuleResponse()
        user_handler = AsyncMock(return_value=response)

        @self.ext.task_modules.submit()
        async def handler(ctx, state, req: TaskModuleRequest):
            return await user_handler(ctx, state, req)

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(
            ActivityTypes.invoke,
            name="task/submit",
            value={"data": {"verb": "v"}, "context": None},
        )
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            assert isinstance(user_handler.call_args[0][2], TaskModuleRequest)
            mock_send.assert_awaited_once_with(ctx, response)

    @pytest.mark.asyncio
    async def test_submit_handler_skips_send_when_none_returned(self):
        @self.ext.task_modules.submit()
        async def handler(ctx, state, req): ...

        route_handler = self.app._routes[0]["handler"]
        ctx = _make_context(ActivityTypes.invoke, name="task/submit", value={})
        with patch(_PATCH, new_callable=AsyncMock) as mock_send:
            await route_handler(ctx, MagicMock())
            mock_send.assert_not_awaited()
