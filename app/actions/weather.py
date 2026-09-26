import httpx
from typing import Any, Dict
from app.actions.base import BaseAction


class WeatherAction(BaseAction):
    """Action to get current weather and forecast for any city using Open-Meteo."""
    
    @property
    def name(self) -> str:
        return "weather"

    @property
    def description(self) -> str:
        return "Get current weather and forecast for any city"

    def _weather_code_to_text(self, code: int) -> str:
        """Map WMO weather codes to human-readable text."""
        if code == 0:
            return "Clear"
        elif 1 <= code <= 3:
            return "Partly cloudy/Overcast"
        elif 45 <= code <= 48:
            return "Fog"
        elif 51 <= code <= 55:
            return "Drizzle"
        elif 61 <= code <= 65:
            return "Rain"
        elif 71 <= code <= 77:
            return "Snow"
        elif 80 <= code <= 82:
            return "Showers"
        elif 95 <= code <= 99:
            return "Thunderstorm"
        return "Unknown"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action")
        if action == "get_weather":
            city = params.get("city")
            if not city:
                return {"success": False, "error": "City parameter is required."}
            
            async with httpx.AsyncClient() as client:
                try:
                    # Geocode the city
                    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
                    geocode_response = await client.get(geocode_url)
                    geocode_response.raise_for_status()
                    geocode_data = geocode_response.json()
                    
                    if not geocode_data.get("results"):
                        return {"success": False, "error": f"City '{city}' not found."}
                    
                    location = geocode_data["results"][0]
                    lat = location["latitude"]
                    lon = location["longitude"]
                    resolved_city = location["name"]
                    
                    # Get weather data
                    weather_url = (
                        f"https://api.open-meteo.com/v1/forecast"
                        f"?latitude={lat}&longitude={lon}"
                        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                        f"&daily=temperature_2m_max,temperature_2m_min,weather_code"
                        f"&timezone=auto&forecast_days=3"
                    )
                    weather_response = await client.get(weather_url)
                    weather_response.raise_for_status()
                    weather_data = weather_response.json()
                    
                    current = weather_data.get("current", {})
                    daily = weather_data.get("daily", {})
                    
                    current_weather = {
                        "temp": current.get("temperature_2m"),
                        "humidity": current.get("relative_humidity_2m"),
                        "wind_speed": current.get("wind_speed_10m"),
                        "condition": self._weather_code_to_text(current.get("weather_code", -1))
                    }
                    
                    forecast = []
                    times = daily.get("time", [])
                    max_temps = daily.get("temperature_2m_max", [])
                    min_temps = daily.get("temperature_2m_min", [])
                    weather_codes = daily.get("weather_code", [])
                    
                    for i in range(len(times)):
                        forecast.append({
                            "date": times[i],
                            "max_temp": max_temps[i] if i < len(max_temps) else None,
                            "min_temp": min_temps[i] if i < len(min_temps) else None,
                            "condition": self._weather_code_to_text(weather_codes[i] if i < len(weather_codes) else -1)
                        })
                    
                    return {
                        "success": True,
                        "city": resolved_city,
                        "current": current_weather,
                        "forecast": forecast
                    }
                    
                except httpx.HTTPError as e:
                    return {"success": False, "error": f"API error occurred: {str(e)}"}
                except Exception as e:
                    return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
