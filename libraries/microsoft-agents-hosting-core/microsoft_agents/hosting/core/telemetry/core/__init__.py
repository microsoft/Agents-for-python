# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from . import resource
from ._agents_telemetry import agents_telemetry
from .type_defs import AttributeMap, SpanCallback
from .simple_span_wrapper import SimpleSpanWrapper
from .base_span_wrapper import BaseSpanWrapper
from .resource import SERVICE_NAME, SERVICE_VERSION, RESOURCE

__all__ = [
    "agents_telemetry",
    "resource",
    "AttributeMap",
    "SpanCallback",
    "SimpleSpanWrapper",
    "BaseSpanWrapper",
    "SERVICE_NAME",
    "SERVICE_VERSION",
    "RESOURCE",
]
