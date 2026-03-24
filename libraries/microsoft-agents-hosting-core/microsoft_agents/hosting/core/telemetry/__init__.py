## DESIGN
# This design is similar to how error codes are implemented and maintained.
# The alternative was to inject all of this telemetry logic inline with the code it instruments.
# While some spans are simple, others require more involved mapping of attributes or
# even emitting metrics.
#
# This design hides the "mess" of telemetry to one location rather than throughout the codebase.
#
# NOTE: this module should not be auto-loaded from __init__.py in order to avoid

from . import attributes
from .core import (
    agents_telemetry,
    SERVICE_NAME,
    SERVICE_VERSION,
    RESOURCE,
    AttributeMap,
    BaseSpanWrapper,
    SimpleSpanWrapper,
)

from .utils import (
    format_scopes,
    get_conversation_id,
    get_delivery_mode,
)

__all__ = [
    "attributes",
    "agents_telemetry",
    "format_scopes",
    "get_conversation_id",
    "get_delivery_mode",
    "AttributeMap",
    "BaseSpanWrapper",
    "SimpleSpanWrapper",
    "SERVICE_NAME",
    "SERVICE_VERSION",
    "RESOURCE",
]
