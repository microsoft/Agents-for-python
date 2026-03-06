
## DESIGN
# This design is similar to how error codes are implemented and maintained.
# The alternative was to inject all of this telemetry logic inline with the code it instruments.
# While some spans are simple, others require more involved mapping of attributes or
# even emitting metrics.
#
# This design hides the "mess" of telemetry to one location rather than throughout the codebase.

from ._agents_telemetry import (
    agents_telemetry,
    _format_scopes
)
from .configure_telemetry import configure_telemetry
from .constants import (
    SERVICE_NAME,
    SERVICE_VERSION,
    RESOURCE
)

__all__ = [
    "agents_telemetry",
    "configure_telemetry",
    "_format_scopes",
    "SERVICE_NAME",
    "SERVICE_VERSION",
    "RESOURCE",
]