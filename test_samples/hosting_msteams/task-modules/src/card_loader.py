# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Helpers for loading Adaptive Card JSON resources bundled with this sample.

Mirrors the .NET ``CardLoader`` utility: it reads a card definition from the
``resources`` directory and optionally substitutes ``{{token}}`` placeholders
before parsing the JSON.
"""

import json
from os import path
from typing import Optional

_RESOURCES_DIR = path.join(path.dirname(__file__), "resources")


def load_card_json(file_name: str, tokens: Optional[dict[str, str]] = None) -> dict:
    """Load a card definition from the resources directory.

    :param file_name: File name of the card JSON (e.g. ``"launcher-card.json"``).
    :param tokens: Optional ``{{token}}`` replacements applied to the raw JSON
        text before parsing.
    :return: The parsed Adaptive Card as a dict.
    """
    with open(path.join(_RESOURCES_DIR, file_name), encoding="utf-8") as handle:
        raw = handle.read()

    if tokens:
        for key, value in tokens.items():
            raw = raw.replace(f"{{{{{key}}}}}", value)

    return json.loads(raw)


def load_resource_text(file_name: str) -> str:
    """Load a raw text resource (e.g. an HTML page) from the resources directory.

    :param file_name: File name of the resource.
    :return: The file contents as text.
    """
    with open(path.join(_RESOURCES_DIR, file_name), encoding="utf-8") as handle:
        return handle.read()
