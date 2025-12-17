# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from urllib.parse import urlparse

from microsoft_agents.activity import AgentsModel


def get_host_and_port(url: str) -> tuple[str, int]:
    """Extract host and port from a URL."""

    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port
    if not host or not port:
        raise ValueError(f"Invalid URL: {url}")
    return host, port


def normalize_model_data(source: AgentsModel | dict) -> dict:
    """Normalize AgentsModel data to a dictionary format."""

    if isinstance(source, AgentsModel):
        return source.model_dump(exclude_unset=True, mode="json")
    return source
