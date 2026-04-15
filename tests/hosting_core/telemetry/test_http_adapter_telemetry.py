# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Telemetry tests for HttpAdapterBase.process_request.

These tests verify which spans are created, what status they receive, and
which metrics fire for each code path through process_request.  Several
tests deliberately assert the *current* (incorrect) behavior for known bugs
so they will fail — and thus catch regressions — once those bugs are fixed.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from opentelemetry import trace

from microsoft_agents.hosting.core.http._http_adapter_base import HttpAdapterBase
from microsoft_agents.hosting.core.telemetry.adapter import constants
from microsoft_agents.hosting.core.telemetry import attributes

from tests._common.fixtures.telemetry import (  # unused imports are needed for fixtures
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from tests._common.telemetry_utils import find_metric, sum_counter, sum_hist_count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _ConcreteAdapter(HttpAdapterBase):
    """Minimal concrete subclass of HttpAdapterBase used in tests."""


def _make_adapter():
    factory = MagicMock()
    factory.create_connector_client = AsyncMock(return_value=MagicMock())
    factory.create_user_token_client = AsyncMock(return_value=MagicMock())
    adapter = _ConcreteAdapter(channel_service_client_factory=factory)
    # Override process_activity so tests don't need real connector clients.
    # Individual tests can replace this with a side_effect.
    adapter.process_activity = AsyncMock(return_value=None)
    return adapter


def _make_request(method="POST", body=None, bad_json=False):
    request = AsyncMock()
    request.method = method
    if bad_json:
        request.json = AsyncMock(side_effect=ValueError("invalid json"))
    else:
        request.json = AsyncMock(
            return_value=body
            or {
                "type": "message",
                "id": "act-1",
                "channelId": "msteams",
                "conversation": {"id": "conv-1"},
                "from": {"id": "user-1"},
                "recipient": {"id": "bot-1"},
            }
        )
    request.get_claims_identity = MagicMock(return_value=None)
    return request


def _make_agent():
    agent = MagicMock()
    agent.on_turn = AsyncMock()
    return agent


def _adapter_process_span(test_exporter):
    return next(
        s
        for s in test_exporter.get_finished_spans()
        if s.name == constants.SPAN_PROCESS
    )


# ---------------------------------------------------------------------------
# Happy path — valid POST with a well-formed activity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_activity_creates_adapter_process_span(test_exporter):
    adapter = _make_adapter()
    await adapter.process_request(_make_request(), _make_agent())

    span_names = [s.name for s in test_exporter.get_finished_spans()]
    assert constants.SPAN_PROCESS in span_names


@pytest.mark.asyncio
async def test_valid_activity_span_status_is_ok(test_exporter):
    adapter = _make_adapter()
    await adapter.process_request(_make_request(), _make_agent())

    span = _adapter_process_span(test_exporter)
    assert span.status.status_code == trace.StatusCode.OK


@pytest.mark.asyncio
async def test_valid_activity_span_has_activity_attributes(test_exporter):
    adapter = _make_adapter()
    await adapter.process_request(_make_request(), _make_agent())

    span = _adapter_process_span(test_exporter)
    assert span.attributes[attributes.ACTIVITY_TYPE] == "message"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "msteams"


@pytest.mark.asyncio
async def test_valid_activity_records_received_metric(test_exporter, test_metric_reader):
    adapter = _make_adapter()
    await adapter.process_request(_make_request(), _make_agent())

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_ACTIVITIES_RECEIVED)) == 1


@pytest.mark.asyncio
async def test_valid_activity_received_metric_has_channel_attribute(
    test_exporter, test_metric_reader
):
    adapter = _make_adapter()
    await adapter.process_request(_make_request(), _make_agent())

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(
        find_metric(data, constants.METRIC_ACTIVITIES_RECEIVED),
        attribute_filter={attributes.ACTIVITY_CHANNEL_ID: "msteams"},
    )
    assert count == 1


# ---------------------------------------------------------------------------
# Non-POST request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_post_request_still_creates_adapter_process_span(test_exporter):
    """The span is entered before the method check, so it fires even for non-POST."""
    adapter = _make_adapter()
    await adapter.process_request(_make_request(method="GET"), _make_agent())

    span_names = [s.name for s in test_exporter.get_finished_spans()]
    assert constants.SPAN_PROCESS in span_names


@pytest.mark.asyncio
async def test_non_post_request_span_status_is_ok(test_exporter):
    """Span exits with OK because the early return is not an exception."""
    adapter = _make_adapter()
    await adapter.process_request(_make_request(method="GET"), _make_agent())

    span = _adapter_process_span(test_exporter)
    assert span.status.status_code == trace.StatusCode.OK


@pytest.mark.asyncio
async def test_non_post_request_fires_received_metric_with_unknown_type(
    test_exporter, test_metric_reader
):
    """BUG: activities_received increments even for non-POST requests because
    share() is never called and the metric fires with UNKNOWN type/channel_id.
    Update this assertion once the bug is fixed."""
    adapter = _make_adapter()
    await adapter.process_request(_make_request(method="GET"), _make_agent())

    data = test_metric_reader.get_metrics_data()
    # BUG: should be 0 — this is not a real activity
    total = sum_counter(find_metric(data, constants.METRIC_ACTIVITIES_RECEIVED))
    assert total == 1

    # The type is UNKNOWN because share() was never called
    unknown_count = sum_counter(
        find_metric(data, constants.METRIC_ACTIVITIES_RECEIVED),
        attribute_filter={attributes.ACTIVITY_TYPE: attributes.UNKNOWN},
    )
    assert unknown_count == 1


# ---------------------------------------------------------------------------
# Bad JSON body
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bad_json_span_status_is_ok(test_exporter):
    """JSON parse error also takes the early-return path — span exits OK."""
    adapter = _make_adapter()
    await adapter.process_request(_make_request(bad_json=True), _make_agent())

    span = _adapter_process_span(test_exporter)
    assert span.status.status_code == trace.StatusCode.OK


@pytest.mark.asyncio
async def test_bad_json_fires_received_metric_with_unknown_type(
    test_exporter, test_metric_reader
):
    """BUG: activities_received fires even when the body is not valid JSON."""
    adapter = _make_adapter()
    await adapter.process_request(_make_request(bad_json=True), _make_agent())

    data = test_metric_reader.get_metrics_data()
    # BUG: should be 0 — no activity was ever parsed
    total = sum_counter(find_metric(data, constants.METRIC_ACTIVITIES_RECEIVED))
    assert total == 1


# ---------------------------------------------------------------------------
# PermissionError — span status bug
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_permission_error_span_reports_ok_not_error(test_exporter):
    """BUG: when process_activity raises PermissionError, the adapter catches it
    inside the AdapterProcess with-block via `except PermissionError: return`.
    Because the exception never propagates through __exit__, the span status is
    set to OK instead of ERROR.  This test documents the current (incorrect)
    behavior — update the assertion to ERROR once the bug is fixed."""
    adapter = _make_adapter()
    adapter.process_activity = AsyncMock(side_effect=PermissionError("not authorized"))

    await adapter.process_request(_make_request(), _make_agent())

    span = _adapter_process_span(test_exporter)
    # BUG: should be ERROR
    assert span.status.status_code == trace.StatusCode.OK


@pytest.mark.asyncio
async def test_permission_error_records_received_metric(test_exporter, test_metric_reader):
    """activities_received fires even when the request was unauthorized."""
    adapter = _make_adapter()
    adapter.process_activity = AsyncMock(side_effect=PermissionError("not authorized"))

    await adapter.process_request(_make_request(), _make_agent())

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_ACTIVITIES_RECEIVED)) == 1


# ---------------------------------------------------------------------------
# Unhandled exception — correct error path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unhandled_exception_span_reports_error(test_exporter):
    """An exception that is NOT caught inside the with-block propagates through
    __exit__ and correctly marks the span ERROR."""
    adapter = _make_adapter()
    adapter.process_activity = AsyncMock(side_effect=RuntimeError("unexpected"))

    with pytest.raises(RuntimeError):
        await adapter.process_request(_make_request(), _make_agent())

    span = _adapter_process_span(test_exporter)
    assert span.status.status_code == trace.StatusCode.ERROR


@pytest.mark.asyncio
async def test_unhandled_exception_records_exception_on_span(test_exporter):
    """Exception details (type, message) are recorded on the span."""
    adapter = _make_adapter()
    adapter.process_activity = AsyncMock(side_effect=RuntimeError("unexpected"))

    with pytest.raises(RuntimeError):
        await adapter.process_request(_make_request(), _make_agent())

    span = _adapter_process_span(test_exporter)
    assert len(span.events) > 0
    exception_event = next(
        (e for e in span.events if e.name == "exception"), None
    )
    assert exception_event is not None


# ---------------------------------------------------------------------------
# AdapterWriteResponse span (invoke path)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invoke_activity_creates_write_response_span(test_exporter):
    """An invoke activity takes the synchronous-response path, which wraps the
    response write in a AdapterWriteResponse span."""
    adapter = _make_adapter()
    invoke_response = MagicMock()
    invoke_response.body = {}
    invoke_response.status = 200
    adapter.process_activity = AsyncMock(return_value=invoke_response)

    await adapter.process_request(
        _make_request(
            body={
                "type": "invoke",
                "id": "act-invoke",
                "channelId": "msteams",
                "conversation": {"id": "conv-1"},
                "from": {"id": "user-1"},
                "recipient": {"id": "bot-1"},
            }
        ),
        _make_agent(),
    )

    span_names = [s.name for s in test_exporter.get_finished_spans()]
    assert constants.SPAN_WRITE_RESPONSE in span_names


@pytest.mark.asyncio
async def test_message_activity_does_not_create_write_response_span(test_exporter):
    """Non-invoke activities return 202 Accepted without a write-response span."""
    adapter = _make_adapter()
    await adapter.process_request(_make_request(), _make_agent())

    span_names = [s.name for s in test_exporter.get_finished_spans()]
    assert constants.SPAN_WRITE_RESPONSE not in span_names
