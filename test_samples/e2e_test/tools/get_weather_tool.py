import random
from pydantic import BaseModel

from agents import function_tool


class Weather(BaseModel):
    city: str
    temperature: str
    conditions: str
    date: str


@function_tool
def get_weather(city: str, date: str) -> Weather:
    temperature = random.randint(8, 21)
    return Weather(
        city=city,
        temperature=f"{temperature}C",
        conditions="Sunny with wind.",
        date=date,
    )
