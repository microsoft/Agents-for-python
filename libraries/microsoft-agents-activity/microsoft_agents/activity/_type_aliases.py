# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Annotated
from pydantic import StringConstraints

NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
