# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class EntityTypes(str, Enum):
    """Well-known enumeration of entity types."""

    GEO_COORDINATES = "GeoCoordinates"
    MENTION = "mention"
    PLACE = "Place"
    THING = "Thing"
    PRODUCT_INFO = "ProductInfo"
