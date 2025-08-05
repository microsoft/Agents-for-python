from typing import Union, Literal
from pydantic import BaseModel

class WeatherForecastAgentResponse(BaseModel):
    contentType: str = Literal["Text", "AdaptiveCard"]
    content: Union[dict, str]