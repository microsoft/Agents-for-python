# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Utility functions for normalizing model data.

Provides functions for converting between BaseModel and dictionary
representations with proper flattening/expansion of nested structures.
"""

from typing import cast
from pydantic import BaseModel
from .backend import expand, flatten

def rename_from_property(data: dict) -> None:
    """Rename keys starting with 'from.' to 'from_property.' for compatibility."""
    mods = {}
    for key in data.keys():
        if key.startswith("from."):
            new_key = key.replace("from.", "from_property.")
            mods[key] = new_key
        elif key == "from":
            new_key = "from_property"
            mods[key] = new_key

    for old_key, new_key in mods.items():
        data[new_key] = data.pop(old_key)

def normalize_model_data(source: BaseModel | dict) -> dict:
    """Normalize a BaseModel or dictionary to an expanded dictionary.

    Converts a BaseModel to a dictionary via ``model_dump``, or expands
    a flat dot-notation dictionary into a nested structure.

    :param source: The BaseModel or dictionary to normalize.
    :return: The normalized dictionary.
    """

    if isinstance(source, BaseModel):
        source = cast(dict, source.model_dump(exclude_unset=True, mode="json"))
        return source
    
    expanded = expand(source)
    rename_from_property(expanded)
    return expanded

def flatten_model_data(source: BaseModel | dict) -> dict:
    """Flatten model data to a single-level dictionary with dot-notation keys.

    Converts a BaseModel or nested dictionary to a flat dictionary
    where nested keys use dot notation (e.g., ``{"from.id": "user-1"}``.

    :param source: The BaseModel or dictionary to flatten.
    :return: A flattened dictionary.
    """

    if isinstance(source, BaseModel):
        source = cast(dict, source.model_dump(exclude_unset=True, mode="json"))
        return flatten(source)
    
    flattened = flatten(source)
    rename_from_property(flattened)
    return flattened