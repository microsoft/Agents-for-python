from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from src.typing_sampler import DropTypingSampler, TYPING_SPAN_NAME


def test_drops_typing_span_and_descendants():
    exporter = InMemorySpanExporter()
    provider = TracerProvider(sampler=DropTypingSampler())
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer(__name__)

    with tracer.start_as_current_span("parent"):
        with tracer.start_as_current_span(TYPING_SPAN_NAME) as typing_span:
            assert not typing_span.is_recording()
            with tracer.start_as_current_span("typing-child") as child_span:
                assert not child_span.is_recording()

        with tracer.start_as_current_span("sibling"):
            pass

    assert {span.name for span in exporter.get_finished_spans()} == {
        "parent",
        "sibling",
    }


def test_samples_unrelated_root_span():
    provider = TracerProvider(sampler=DropTypingSampler())
    tracer = provider.get_tracer(__name__)

    with tracer.start_as_current_span("unrelated") as span:
        assert span.is_recording()
