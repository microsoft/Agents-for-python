from pydantic import BaseModel
from typing import Optional


class TabSubmitData(BaseModel):
    """Invoke ('tab/submit') request value payload data.

    :param type: Currently, 'tab/submit'.
    :type type: str
    :param properties: Gets or sets properties that are not otherwise defined by the TabSubmit
     type but that might appear in the serialized REST JSON object.
    :type properties: object
    """

    type: str
    properties: Optional[object]
