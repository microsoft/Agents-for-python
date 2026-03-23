## DESIGN
# This design is similar to how error codes are implemented and maintained.
# The alternative was to inject all of this telemetry logic inline with the code it instruments.
# While some spans are simple, others require more involved mapping of attributes or
# even emitting metrics.
#
# This design hides the "mess" of telemetry to one location rather than throughout the codebase.
#
# NOTE: this module should not be auto-loaded from __init__.py in order to avoid

from .core._agents_telemetry import (
    agents_telemetry,
)
from .core import SERVICE_NAME, SERVICE_VERSION, RESOURCE
from .utils import _format_scopes

__all__ = [
    "agents_telemetry",
    "_format_scopes",
    "SERVICE_NAME",
    "SERVICE_VERSION",
    "RESOURCE",
]
