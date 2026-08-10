from typing import Mapping, Callable

from opentelemetry.util.types import AttributeValue
from opentelemetry.trace import Span, Link

AttributeMap = Mapping[str, AttributeValue]
SpanCallback = Callable[[Span, float, Exception | None], None]