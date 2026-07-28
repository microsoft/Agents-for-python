# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .env_group import env_group

# force modules to load, allowing CLI registration
from . import _show
from . import _help

__all__ = ["env_group"]
