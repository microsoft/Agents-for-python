# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import cast
from pydantic import BaseModel
from .backend import expand

def normalize_model_data(source: BaseModel | dict) -> dict:
    """Normalize AgentsModel data to a dictionary format.

    Creates a deep copy if the source is a dictionary.

    :param source: The AgentsModel or dictionary to normalize.
    :return: The normalized dictionary.
    """

    if isinstance(source, BaseModel):
        source = cast(dict, source.model_dump(exclude_unset=True, mode="json"))
        return source
    
    return expand(source)