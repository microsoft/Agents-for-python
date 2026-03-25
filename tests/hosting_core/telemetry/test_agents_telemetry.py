from opentelemetry import trace

from tests._common.fixtures.telemetry import ( # unused imports are needed for fixtures
    test_telemetry,
    test_exporter,
    test_metric_reader,
)

from tests._common.telemetry_utils import find_metric, sum_counter

from microsoft_agents.hosting.core.telemetry import (
    agents_telemetry, 
    SERVICE_NAME,
    SERVICE_VERSION,
)

def test_tracer(test_exporter):
    """Test that the tracer is initialized with the correct service name and version."""

    with agents_telemetry.tracer.start_as_current_span("test_span"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "test_span"
    assert spans[0].instrumentation_scope.name == SERVICE_NAME
    assert spans[0].instrumentation_scope.version == SERVICE_VERSION

def test_meter(test_metric_reader):
    """Test that the meter is initialized with the correct service name and version."""
    counter = agents_telemetry.meter.create_counter("test_counter")
    counter.add(1)

    metrics_data = test_metric_reader.get_metrics_data()
    metric = find_metric(metrics_data, "test_counter")
    assert len(metric.data.data_points) == 1
    assert sum_counter(metric) == 1
    assert metric.name == "test_counter"

def test_start_as_current_span(test_exporter):
    """Test start_as_current_span creates a span with context attributes."""

    with agents_telemetry.start_as_current_span("test_span"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "test_span"
    assert spans[0].instrumentation_scope.name == SERVICE_NAME
    assert spans[0].instrumentation_scope.version == SERVICE_VERSION

def test_start_as_current_span_with_callback(mocker, test_exporter):
    """Test start_as_current_span records success status and callback payload."""
    callback = mocker.Mock()

    with agents_telemetry.start_as_current_span(
        "test_span",
        callback=callback,
    ):
        pass

    finished_spans = test_exporter.get_finished_spans()
    assert len(finished_spans) == 1

    finished_span = finished_spans[0]
    assert finished_span.name == "test_span"
    assert finished_span.status.status_code == trace.StatusCode.OK

    callback.assert_called_once()
    callback_span, duration_ms, callback_exception = callback.call_args.args
    assert callback_span.name == "test_span"
    assert duration_ms >= 0
    assert callback_exception is None

def test_start_as_current_span_with_callback_with_failure(mocker, test_exporter):
    """Test start_as_current_span records failure status and callback payload."""
    callback = mocker.Mock()

    exception_raised = False
    try:
        with agents_telemetry.start_as_current_span(
            "test_span",
            callback=callback,
        ):
            raise ValueError("Test exception")
    except ValueError as ex:
        exception_raised = True
        assert str(ex) == "Test exception"

    assert exception_raised
    
    finished_spans = test_exporter.get_finished_spans()
    assert len(finished_spans) == 1

    finished_span = finished_spans[0]
    assert finished_span.name == "test_span"
    assert finished_span.status.status_code == trace.StatusCode.ERROR

    callback.assert_called_once()
    callback_span, duration_ms, callback_exception = callback.call_args.args
    assert callback_span.name == "test_span"
    assert duration_ms >= 0
    assert callback_exception is not None
    assert str(callback_exception) == "Test exception"