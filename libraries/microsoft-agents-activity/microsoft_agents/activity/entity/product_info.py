# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Literal

from .entity import Entity
from .entity_types import EntityTypes


class ProductInfo(Entity):
    """Product information (entity type: "productInfo").

    :param type: The type of the entity, always "productInfo".
    :type type: str
    :param id: The unique identifier for the product.
    :type id: str
    """

    type: Literal[EntityTypes.PRODUCT_INFO] = EntityTypes.PRODUCT_INFO
    id: str = None
