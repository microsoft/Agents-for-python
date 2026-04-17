# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass


@dataclass
class Citation:
    """Citations returned by the model."""

    content: str
    """The content of the citation."""

    title: str | None = None
    """The title of the citation."""

    url: str | None = None
    """The URL of the citation."""

    filepath: str | None = None
    """The filepath of the document."""
