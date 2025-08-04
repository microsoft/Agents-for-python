import random
import logging
from pydantic import BaseModel
from datetime import datetime

from agents import function_tool

logger = logging.getLogger(__name__)


class Weather(BaseModel):
    city: str
    temperature: str
    conditions: str
    date: str


@function_tool
def get_date() -> str:
    """
    A function tool that returns the current date and time.
    """
    return datetime.now().isoformat()


@function_tool
def get_weather(city: str, date: str) -> Weather:
    logger.debug(f"get_weather called with city: {city}, date: {date}")
    temperature = random.randint(8, 21)
    return Weather(
        city=city,
        temperature=f"{temperature}C",
        conditions="Sunny with wind.",
        date=date,
    )
