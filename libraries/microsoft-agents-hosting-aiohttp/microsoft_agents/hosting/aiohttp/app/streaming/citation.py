# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Optional
from dataclasses import dataclass


@dataclass
class Citation:
    """Citations returned by the model."""

    content: str
    """The content of the citation."""

    title: Optional[str] = None
    """The title of the citation."""

    url: Optional[str] = None
    """The URL of the citation."""

    filepath: Optional[str] = None
    """The filepath of the document."""
