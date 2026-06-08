# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum

class SDKVersion(str, Enum):

    PYTHON = "python"
    NODEJS = "nodejs"
    DOTNET = "dotnet"