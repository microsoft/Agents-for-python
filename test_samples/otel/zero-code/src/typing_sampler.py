from collections.abc import Sequence

from opentelemetry.context import Context
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    Sampler,
    SamplingResult,
)
from opentelemetry.trace import Link, SpanKind, get_current_span
from opentelemetry.trace.span import TraceState
from opentelemetry.util.types import Attributes
from microsoft_agents.hosting.core.app.telemetry import constants

TYPING_SPAN_NAME = constants.SPAN_SEND_TYPING


class DropTypingSampler(Sampler):
    """Drop typing spans and descendants while sampling other root spans."""

    def __init__(self, _argument: str | None = None) -> None:
        pass

    def should_sample(
        self,
        parent_context: Context | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        trace_state: TraceState | None = None,
    ) -> SamplingResult:
        parent_span_context = get_current_span(parent_context).get_span_context()
        delegate = (
            ALWAYS_OFF
            if name == TYPING_SPAN_NAME
            or (
                parent_span_context.is_valid
                and not parent_span_context.trace_flags.sampled
            )
            else ALWAYS_ON
        )
        return delegate.should_sample(
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state,
        )

    def get_description(self) -> str:
        return "DropTypingSampler"
