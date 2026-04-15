from types import SimpleNamespace

from microsoft_agents.activity import Activity, ConversationAccount, ChannelAccount
from microsoft_agents.hosting.core.telemetry import attributes
from microsoft_agents.hosting.core.app.telemetry.spans import (
    AppOnTurn,
    AppRouteHandler,
    AppBeforeTurn,
    AppAfterTurn,
    AppDownloadFiles,
)
from microsoft_agents.hosting.core.app.telemetry import constants

from tests._common.fixtures.telemetry import (
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from tests._common.telemetry_utils import find_metric, sum_counter, sum_hist_count


def _make_context(**activity_overrides):
    defaults = dict(
        type="message",
        channel_id="msteams",
        service_url="https://smba.trafficmanager.net/teams/",
        conversation=ConversationAccount(id="conv-1"),
        from_property=ChannelAccount(id="user-1"),
        recipient=ChannelAccount(id="bot-1"),
    )
    defaults.update(activity_overrides)
    activity = Activity(**defaults)
    return SimpleNamespace(activity=activity)


# ---- AppOnTurn ----


def test_app_on_turn_creates_span(test_exporter):
    ctx = _make_context()

    with AppOnTurn(ctx):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_ON_TURN


def test_app_on_turn_span_attributes(test_exporter):
    ctx = _make_context(id="act-1")

    with AppOnTurn(ctx):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_TYPE] == "message"
    assert span.attributes[attributes.ACTIVITY_ID] == "act-1"


def test_app_on_turn_span_attributes_missing_id(test_exporter):
    ctx = _make_context()

    with AppOnTurn(ctx):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ACTIVITY_TYPE] == "message"
    assert span.attributes[attributes.ACTIVITY_ID] == attributes.UNKNOWN


def test_app_on_turn_records_turn_metrics(test_exporter, test_metric_reader):
    ctx = _make_context()

    with AppOnTurn(ctx):
        pass

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(find_metric(data, constants.METRIC_TURN_COUNT))
    assert count == 1
    duration = sum_hist_count(find_metric(data, constants.METRIC_TURN_DURATION))
    assert duration == 1


def test_app_on_turn_records_error_metric_on_exception(
    test_exporter, test_metric_reader
):
    ctx = _make_context()

    try:
        with AppOnTurn(ctx):
            raise ValueError("boom")
    except ValueError:
        pass

    data = test_metric_reader.get_metrics_data()
    error_count = sum_counter(find_metric(data, constants.METRIC_TURN_ERROR_COUNT))
    assert error_count == 1
    # success counter should NOT be incremented
    success_count = sum_counter(find_metric(data, constants.METRIC_TURN_COUNT))
    assert success_count == 0


def test_app_on_turn_records_turn_duration_on_error(
    test_exporter, test_metric_reader
):
    """turn_duration is recorded on both success and error paths."""
    ctx = _make_context()

    try:
        with AppOnTurn(ctx):
            raise ValueError("boom")
    except ValueError:
        pass

    data = test_metric_reader.get_metrics_data()
    duration_count = sum_hist_count(find_metric(data, constants.METRIC_TURN_DURATION))
    assert duration_count == 1


def test_app_on_turn_share(test_exporter):
    ctx = _make_context()

    with AppOnTurn(ctx) as wrapper:
        wrapper.share(route_authorized=True, route_matched=False)

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ROUTE_AUTHORIZED] is True
    assert span.attributes[attributes.ROUTE_MATCHED] is False


# ---- AppRouteHandler ----


def test_app_route_handler_creates_span(test_exporter):
    with AppRouteHandler(is_invoke=False, is_agentic=False):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_ROUTE_HANDLER


def test_app_route_handler_span_attributes(test_exporter):
    with AppRouteHandler(is_invoke=True, is_agentic=True):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ROUTE_IS_INVOKE] is True
    assert span.attributes[attributes.ROUTE_IS_AGENTIC] is True


def test_app_route_handler_not_invoke_not_agentic(test_exporter):
    with AppRouteHandler(is_invoke=False, is_agentic=False):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ROUTE_IS_INVOKE] is False
    assert span.attributes[attributes.ROUTE_IS_AGENTIC] is False


# ---- AppBeforeTurn ----


def test_app_before_turn_creates_span(test_exporter):
    with AppBeforeTurn():
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_BEFORE_TURN


# ---- AppAfterTurn ----


def test_app_after_turn_creates_span(test_exporter):
    with AppAfterTurn():
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_AFTER_TURN


# ---- AppDownloadFiles ----


def test_app_download_files_creates_span(test_exporter):
    ctx = _make_context()
    ctx.activity.attachments = []

    with AppDownloadFiles(ctx):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_DOWNLOAD_FILES


def test_app_download_files_attachment_count(test_exporter):
    ctx = _make_context()
    ctx.activity.attachments = [SimpleNamespace(), SimpleNamespace(), SimpleNamespace()]

    with AppDownloadFiles(ctx):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ATTACHMENT_COUNT] == 3


def test_app_download_files_no_attachments(test_exporter):
    ctx = _make_context()
    ctx.activity.attachments = None

    with AppDownloadFiles(ctx):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ATTACHMENT_COUNT] == 0
