import time

import pytest
from types import SimpleNamespace

from opentelemetry.trace import StatusCode

from tests._common.fixtures.telemetry import ( # unused imports are needed for fixtures
    test_telemetry,
    test_exporter,
    test_metric_reader,
    clear
)
from tests._common.telemetry_utils import (
    _find_metric,
    _sum_counter,
    _sum_hist_count,
)

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.telemetry import (
    agents_telemetry,
    SimpleSpanWrapper,
)


class MySpanWrapper(SimpleSpanWrapper):
    """Subclass with custom attributes and a callback that records info on the span."""

    def __init__(self, span_name):
        super().__init__(span_name)

    def _callback(self, span, duration_ms, exception):
        span.set_attribute("callback_called", True)
        span.set_attribute("duration_ms", duration_ms)
        if exception:
            span.set_attribute("exception_message", str(exception))
    
    def _get_attributes(self):
        return {"custom_attribute": "custom_value"}


class MinimalSpanWrapper(SimpleSpanWrapper):
    """Subclass that uses default (no-op) _callback and empty _get_attributes."""

    def __init__(self, span_name):
        super().__init__(span_name)


class TestSimpleSpanWrapper:
    def test_simple_span_wrapper(self, test_exporter):
        """Test that MySpanWrapper creates a span with the correct attributes and callback."""
        with MySpanWrapper("test_simple_span"):
            pass

        spans = test_exporter.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.name == "test_simple_span"
        assert span.attributes["custom_attribute"] == "custom_value"
        assert span.attributes["callback_called"] is True
        assert span.attributes["duration_ms"] >= 0

    def test_minimal_span_wrapper_creates_span(self, test_exporter):
        """A subclass with no overrides still creates a valid span."""
        with MinimalSpanWrapper("minimal_span"):
            pass

        spans = test_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "minimal_span"

    def test_minimal_span_no_custom_attributes(self, test_exporter):
        """Default _get_attributes returns empty dict, so no custom attributes are set."""
        with MinimalSpanWrapper("no_attrs"):
            pass

        span = test_exporter.get_finished_spans()[0]
        # The span should not have the custom_attribute key
        assert "custom_attribute" not in (span.attributes or {})

    def test_span_status_ok_on_success(self, test_exporter):
        """Span status is OK when the body completes without error."""
        with MySpanWrapper("ok_span"):
            pass

        span = test_exporter.get_finished_spans()[0]
        assert span.status.status_code == StatusCode.OK

    def test_span_status_error_on_exception(self, test_exporter):
        """Span status is ERROR and exception is re-raised when body raises."""
        with pytest.raises(ValueError, match="boom"):
            with MySpanWrapper("err_span"):
                raise ValueError("boom")

        span = test_exporter.get_finished_spans()[0]
        assert span.status.status_code == StatusCode.ERROR

    def test_callback_receives_exception(self, test_exporter):
        """The callback receives the exception object when the body raises."""
        with pytest.raises(RuntimeError):
            with MySpanWrapper("cb_err"):
                raise RuntimeError("fail")

        span = test_exporter.get_finished_spans()[0]
        assert span.attributes["callback_called"] is True
        assert span.attributes["exception_message"] == "fail"

    def test_exception_is_recorded_on_span(self, test_exporter):
        """record_exception is called, so the span events contain the exception."""
        with pytest.raises(TypeError):
            with MySpanWrapper("rec_exc"):
                raise TypeError("type error")

        span = test_exporter.get_finished_spans()[0]
        exception_events = [e for e in span.events if e.name == "exception"]
        assert len(exception_events) == 1
        assert "type error" in exception_events[0].attributes["exception.message"]

    def test_span_completion_event_on_success(self, test_exporter):
        """A completion event is added on successful span execution."""
        with MinimalSpanWrapper("evt_span"):
            pass

        span = test_exporter.get_finished_spans()[0]
        completion_events = [e for e in span.events if "completed" in e.name]
        assert len(completion_events) == 1
        assert completion_events[0].attributes["duration_ms"] >= 0

    def test_no_completion_event_on_failure(self, test_exporter):
        """No completion event is added when the span body raises."""
        with pytest.raises(Exception):
            with MinimalSpanWrapper("no_evt"):
                raise Exception("oops")

        span = test_exporter.get_finished_spans()[0]
        completion_events = [e for e in span.events if "completed" in e.name]
        assert len(completion_events) == 0

    def test_duration_is_positive(self, test_exporter):
        """The callback's duration_ms reflects actual elapsed time."""
        with MySpanWrapper("dur_span"):
            time.sleep(0.05)

        span = test_exporter.get_finished_spans()[0]
        assert span.attributes["duration_ms"] >= 40  # at least ~40ms

    def test_active_property_inside_context(self, test_exporter):
        """The active property is True while the context manager is open."""
        wrapper = MySpanWrapper("active_test")
        assert wrapper.active is False

        with wrapper:
            assert wrapper.active is True

        assert wrapper.active is False

    def test_otel_span_accessible_inside_context(self, test_exporter):
        """otel_span returns the underlying span while active."""
        wrapper = MinimalSpanWrapper("otel_access")
        with wrapper:
            otel_span = wrapper.otel_span
            assert otel_span is not None

    def test_otel_span_raises_when_not_started(self):
        """Accessing otel_span before start raises RuntimeError."""
        wrapper = MinimalSpanWrapper("not_started")
        with pytest.raises(RuntimeError):
            _ = wrapper.otel_span

    def test_start_end_manual_lifecycle(self, test_exporter):
        """start() and end() can be used instead of the context manager."""
        wrapper = MySpanWrapper("manual_lifecycle")
        wrapper.start()
        assert wrapper.active is True
        wrapper.end()
        assert wrapper.active is False

        spans = test_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "manual_lifecycle"

    def test_multiple_sequential_spans(self, test_exporter):
        """Multiple span wrappers used sequentially each create their own span."""
        with MySpanWrapper("seq_1"):
            pass
        with MySpanWrapper("seq_2"):
            pass
        with MinimalSpanWrapper("seq_3"):
            pass

        spans = test_exporter.get_finished_spans()
        assert len(spans) == 3
        names = [s.name for s in spans]
        assert "seq_1" in names
        assert "seq_2" in names
        assert "seq_3" in names

    def test_nested_span_wrappers(self, test_exporter):
        """Nested span wrappers create parent-child span relationships."""
        with MySpanWrapper("parent"):
            with MinimalSpanWrapper("child"):
                pass

        spans = test_exporter.get_finished_spans()
        assert len(spans) == 2
        child_span = next(s for s in spans if s.name == "child")
        parent_span = next(s for s in spans if s.name == "parent")
        assert child_span.parent.span_id == parent_span.context.span_id

    def test_wrapper_reuse_after_end(self, test_exporter):
        """A wrapper can be reused after it has been ended."""
        wrapper = MySpanWrapper("reuse")

        with wrapper:
            pass
        assert wrapper.active is False

        # Re-enter
        with wrapper:
            assert wrapper.active is True
        assert wrapper.active is False

        spans = test_exporter.get_finished_spans()
        assert len(spans) == 2
        assert all(s.name == "reuse" for s in spans)

    def test_custom_attributes_set_on_span(self, test_exporter):
        """Custom attributes from _get_attributes appear on the finished span."""

        class MultiAttrWrapper(SimpleSpanWrapper):
            def __init__(self):
                super().__init__("multi_attr")

            def _get_attributes(self):
                return {"key_a": "val_a", "key_b": 42, "key_c": True}

        with MultiAttrWrapper():
            pass

        span = test_exporter.get_finished_spans()[0]
        assert span.attributes["key_a"] == "val_a"
        assert span.attributes["key_b"] == 42
        assert span.attributes["key_c"] is True

    def test_exception_propagates_unchanged(self, test_exporter):
        """The original exception type and message are preserved after re-raise."""

        class CustomError(Exception):
            pass

        with pytest.raises(CustomError, match="custom msg"):
            with MinimalSpanWrapper("propagate"):
                raise CustomError("custom msg")