# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Mapping

from microsoft_agents.activity.config import Configuration
from microsoft_agents.activity.config._metadata import _RootConfigMetadata


def create_configuration(
    values: Mapping | None = None,
    *,
    is_root: bool = False,
    _base_path: str | None = None,
) -> Configuration:
    """Build unit-test input without coupling root binding to source resolution."""
    config = Configuration(values, _base_path=_base_path)
    if is_root:
        _RootConfigMetadata.set(config, True)
    return config
