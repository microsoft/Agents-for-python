import os

from opentelemetry.sdk.resources import Resource

SERVICE_NAME = "microsoft_agents"
SERVICE_VERSION = "1.0.0"

RESOURCE = Resource.create(
    {
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        "telemetry.sdk.language": "python",
    }
)