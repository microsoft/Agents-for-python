# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class EntityTypes(StrEnum):
    """Well-known enumeration of entity types."""

    ACTIVITY_TREATMENT = "activityTreatment"
    AI_CITATION = "https://schema.org/Message"
    GEO_COORDINATES = "GeoCoordinates"
    MENTION = "mention"
    PLACE = "Place"
    THING = "Thing"
    PRODUCT_INFO = "ProductInfo"
    STREAM_INFO = "streaminfo"
