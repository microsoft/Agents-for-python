# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import MemoryStorage, TurnContext
from microsoft_agents.hosting.core.app import (
    AgentApplication,
    ApplicationOptions,
    InputFile,
    InputFileDownloader,
    TurnState,
)
from microsoft_agents.hosting.core.app.oauth import Authorization
from tests._common.testing_objects import (
    TestingConnectionManager as _ConnectionManager,
)


class DummyFileDownloader(InputFileDownloader):
    def __init__(
        self,
        files: list[InputFile],
        calls: list[str] | None = None,
        name: str = "downloader",
    ):
        self.files = files
        self.calls = calls if calls is not None else []
        self.name = name
        self.contexts: list[TurnContext] = []

    async def download_files(self, context: TurnContext) -> list[InputFile]:
        self.calls.append(self.name)
        self.contexts.append(context)
        return self.files


class StubAdapter:
    pass


def _make_activity() -> Activity:
    return Activity(
        type=ActivityTypes.event,
        channel_id="test",
        conversation={"id": "conversation-id"},
        from_property={"id": "user-id"},
    )


def _make_app(
    file_downloaders: list[InputFileDownloader] | None = None,
) -> AgentApplication[TurnState]:
    storage = MemoryStorage()
    return AgentApplication[TurnState](
        options=ApplicationOptions(
            storage=storage,
            start_typing_timer=False,
            remove_recipient_mention=False,
            file_downloaders=file_downloaders or [],
        ),
        authorization=Authorization(
            storage=storage,
            connection_manager=_ConnectionManager(),
        ),
    )


@pytest.mark.asyncio
async def test_file_downloader_runs_after_before_turn_and_before_route():
    calls: list[str] = []
    downloaded_file = InputFile(
        content=b"file-content",
        content_type="text/plain",
        filename="document.txt",
    )
    downloader = DummyFileDownloader([downloaded_file], calls)
    app = _make_app([downloader])
    context = TurnContext(StubAdapter(), _make_activity())
    files_seen_by_route: list[InputFile] = []

    async def before_turn(_context: TurnContext, state: TurnState):
        calls.append("before")
        assert state.temp.input_files == []
        return True

    app.before_turn(before_turn)

    @app.activity(ActivityTypes.event)
    async def on_event(_context: TurnContext, state: TurnState):
        calls.append("route")
        files_seen_by_route.extend(state.temp.input_files)

    await app.on_turn(context)

    assert calls == ["before", "downloader", "route"]
    assert downloader.contexts == [context]
    assert files_seen_by_route == [downloaded_file]


@pytest.mark.asyncio
async def test_multiple_file_downloaders_combine_results_in_registration_order():
    first_file = InputFile(
        content=b"first",
        content_type="text/plain",
        filename="first.txt",
    )
    second_file = InputFile(
        content=b"second",
        content_type="text/plain",
        filename="second.txt",
    )
    calls: list[str] = []
    app = _make_app(
        [
            DummyFileDownloader([first_file], calls, "first"),
            DummyFileDownloader([second_file], calls, "second"),
        ]
    )
    files_seen_by_route: list[InputFile] = []

    @app.activity(ActivityTypes.event)
    async def on_event(_context: TurnContext, state: TurnState):
        files_seen_by_route.extend(state.temp.input_files)

    await app.on_turn(TurnContext(StubAdapter(), _make_activity()))

    assert calls == ["first", "second"]
    assert files_seen_by_route == [first_file, second_file]


@pytest.mark.asyncio
async def test_route_receives_empty_input_files_when_no_downloaders_are_configured():
    app = _make_app()
    files_seen_by_route: list[InputFile] | None = None

    @app.activity(ActivityTypes.event)
    async def on_event(_context: TurnContext, state: TurnState):
        nonlocal files_seen_by_route
        files_seen_by_route = state.temp.input_files

    await app.on_turn(TurnContext(StubAdapter(), _make_activity()))

    assert files_seen_by_route == []
