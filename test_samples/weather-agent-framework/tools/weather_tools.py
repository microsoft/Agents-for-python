"""Weather lookup tools using OpenWeatherMap API."""
from os import environ
from typing import Annotated, Dict, List
from pydantic import Field
from pyowm import OWM
from pyowm.weatherapi30.weather import Weather
from pyowm.weatherapi30.forecast import Forecast


def get_current_weather_for_location(
    location: Annotated[str, Field(description="The city name")],
    state: Annotated[str, Field(description="The US state name or empty string for international cities")]
) -> str:
    """
    Retrieves the current weather for a specified location.

    This function uses the OpenWeatherMap API to fetch current weather data for a given city and state.

    Args:
        location: The name of the city for which to retrieve the weather.
        state: The name of the state where the city is located (US only, empty for international).

    Returns:
        A formatted string containing the current weather details including temperature,
        conditions, humidity, and wind speed.

    Raises:
        ValueError: If the location cannot be found or API key is invalid.
    """
    print(f"Looking up current weather in {location}, {state if state else 'international'}")

    try:
        # Initialize OpenWeatherMap client
        owm = OWM(environ["OPENWEATHER_API_KEY"])
        mgr = owm.weather_manager()

        # Build location query
        query = f"{location},{state},US" if state else location

        # Get current weather
        observation = mgr.weather_at_place(query)
        weather: Weather = observation.weather

        # Extract weather details
        temp = weather.temperature('fahrenheit')
        current_temp = temp.get('temp', 'N/A')
        temp_min = temp.get('temp_min', 'N/A')
        temp_max = temp.get('temp_max', 'N/A')

        humidity = weather.humidity
        wind = weather.wind().get('speed', 'N/A')
        status = weather.detailed_status

        # Format response
        result = f"""Current Weather for {location}, {state if state else 'international'}:
- Temperature: {current_temp}°F
- Low: {temp_min}°F / High: {temp_max}°F
- Conditions: {status.capitalize()}
- Humidity: {humidity}%
- Wind Speed: {wind} mph"""

        print(f"Successfully retrieved weather for {location}")
        return result

    except Exception as e:
        error_msg = f"Unable to retrieve weather for {location}, {state}: {str(e)}"
        print(error_msg)
        return error_msg


def get_weather_forecast_for_location(
    location: Annotated[str, Field(description="The city name")],
    state: Annotated[str, Field(description="The US state name or empty string for international cities")]
) -> str:
    """
    Retrieves the 5-day weather forecast for a specified location.

    This function uses the OpenWeatherMap API to fetch forecast data for a given city and state.

    Args:
        location: The name of the city for which to retrieve the forecast.
        state: The name of the state where the city is located (US only, empty for international).

    Returns:
        A formatted string containing the 5-day forecast with dates, temperatures, and conditions.

    Raises:
        ValueError: If the location cannot be found or API key is invalid.
    """
    print(f"Looking up weather forecast in {location}, {state if state else 'international'}")

    try:
        # Initialize OpenWeatherMap client
        owm = OWM(environ["OPENWEATHER_API_KEY"])
        mgr = owm.weather_manager()

        # Build location query
        query = f"{location},{state},US" if state else location

        # Get forecast
        forecast: Forecast = mgr.forecast_at_place(query, '3h').forecast

        # Process forecast data - get daily forecasts
        daily_forecasts: Dict[str, List[Weather]] = {}

        for weather in forecast.weathers:
            date_str = weather.reference_time('iso').split('T')[0]
            if date_str not in daily_forecasts:
                daily_forecasts[date_str] = []
            daily_forecasts[date_str].append(weather)

        # Format forecast for up to 5 days
        result_lines = [f"5-Day Weather Forecast for {location}, {state if state else 'international'}:\n"]

        for i, (date, weathers) in enumerate(list(daily_forecasts.items())[:5]):
            # Get temperature range for the day
            temps = [w.temperature('fahrenheit').get('temp', 0) for w in weathers]
            temp_min = min(temps) if temps else 'N/A'
            temp_max = max(temps) if temps else 'N/A'

            # Get most common weather condition
            statuses = [w.detailed_status for w in weathers]
            status = max(set(statuses), key=statuses.count) if statuses else 'Unknown'

            result_lines.append(
                f"Day {i+1} ({date}):\n"
                f"  Low: {temp_min:.1f}°F / High: {temp_max:.1f}°F\n"
                f"  Conditions: {status.capitalize()}"
            )

        result = "\n".join(result_lines)
        print(f"Successfully retrieved forecast for {location}")
        return result

    except Exception as e:
        error_msg = f"Unable to retrieve forecast for {location}, {state}: {str(e)}"
        print(error_msg)
        return error_msg
