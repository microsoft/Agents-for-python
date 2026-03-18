# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Literal

from .._type_aliases import NonEmptyString
from .entity import Entity
from .entity_types import EntityTypes


class StreamInfo(Entity):

    type: str = EntityTypes.STREAM_INFO.value

    stream_type: NonEmptyString = "streaming"
    stream_sequence: int

    stream_id: str = ""
    stream_result: str = ""

    feedback_loop_enabled: bool = False
    feedback_loop: dict | None = None
