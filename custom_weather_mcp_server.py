from mcp.server.fastmcp import FastMCP
import requests
import os 
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Weather MCP Server")


OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
REQUEST_TIMEOUT_SECONDS = 10


def _get_weather_data(url: str, city: str) -> dict:
    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY is not configured."}

    try:
        response = requests.get(
            url,
            params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {"error": "Weather service is temporarily unavailable."}
    except ValueError:
        return {"error": "Weather service returned an invalid response."}


@mcp.tool()
def get_current_weather(city: str):

    data = _get_weather_data("https://api.openweathermap.org/data/2.5/weather", city)
    if "error" in data:
        return data

    return {
        "city": data["name"],
        "temperature_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["description"],
        "wind_speed": data["wind"]["speed"]
    }



@mcp.tool()
def get_forecast(city: str):

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
    )

    data = _get_weather_data(url, city)
    if "error" in data:
        return data

    forecast = []

    # Return first 5 forecast entries
    for item in data.get("list", [])[:5]:

        forecast.append(
            {
                "datetime": item["dt_txt"],
                "temperature": item["main"]["temp"],
                "weather": item["weather"][0]["description"]
            }
        )

    return {
        "city": city,
        "forecast": forecast
    }




if __name__ == "__main__":
    mcp.run()
