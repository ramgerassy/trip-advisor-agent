"""
Weather tool using Open-Meteo free API.
"""
import logging
from datetime import datetime, date
from typing import List, Optional

import httpx
from app.tools.base import BaseTool, ToolResult
from app.core.config import settings
from app.core.llm_client import get_factual_llm

logger = logging.getLogger(__name__)


class WeatherTool(BaseTool):
    """Tool for getting weather forecasts using Open-Meteo API."""
    
    def __init__(self):
        super().__init__("weather", cache_ttl_hours=settings.CACHE_TTL_HOURS)
        self.base_url = settings.OPENMETEO_BASE_URL
        self.timeout = settings.TOOL_TIMEOUT_SECONDS
        self.factual_llm = get_factual_llm()
    
    def _validate_dates(self, start_date: str, end_date: str) -> tuple[bool, str]:
        """Validate date inputs."""
        try:
            start = datetime.fromisoformat(start_date).date()
            end = datetime.fromisoformat(end_date).date()
            
            today = date.today()
            
            # Check date order
            if start > end:
                return False, "Start date must be before end date"
            
            # Check if dates are not too far in the past
            if start < today and (today - start).days > 1:
                return False, "Cannot get weather data for past dates"
            
            # Check if dates are not too far in the future (Open-Meteo limit ~16 days)
            if start > today and (start - today).days > 14:
                return False, "Weather forecast only available for next 14 days"
            
            # Check trip length (reasonable limit)
            if (end - start).days > 30:
                return False, "Trip length too long for weather forecast"
            
            return True, ""
            
        except ValueError as e:
            return False, f"Invalid date format: {str(e)}"
    
    def _get_coordinates_from_api(self, city: str) -> tuple[Optional[float], Optional[float], str]:
        """
        Get coordinates for a city using Open-Meteo geocoding API.
        Returns (latitude, longitude, location_name)
        """
        try:
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(geocoding_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if not data.get("results"):
                return None, None, f"Location '{city}' not found in geocoding API"
            
            result = data["results"][0]
            return (
                result["latitude"], 
                result["longitude"], 
                f"{result['name']}, {result.get('country', '')}"
            )
            
        except Exception as e:
            logger.warning(f"Geocoding API failed for {city}: {e}")
            return None, None, f"Geocoding API error: {str(e)}"
    
    def _get_coordinates_from_llm(self, city: str) -> tuple[Optional[float], Optional[float], str]:
        """
        Get coordinates from LLM as fallback.
        Returns (latitude, longitude, location_name)
        """
        try:
            prompt = f"""What are the latitude and longitude coordinates for {city}?

IMPORTANT: If you don't know the exact coordinates or are unsure, respond with "none".
Only provide coordinates if you are confident they are accurate.

Format your response as:
latitude: [number]
longitude: [number]
location: [full location name with country]

Example:
latitude: 48.8566
longitude: 2.3522
location: Paris, France"""

            response = self.factual_llm.invoke(prompt)
            logger.debug(f"LLM geocoding response for {city}: {response}")
            
            # Parse the response
            lines = response.strip().lower().split('\n')
            lat, lon, location = None, None, city
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('none') or 'none' in line:
                    return None, None, f"LLM doesn't know coordinates for '{city}'"
                
                if line.startswith('latitude:'):
                    try:
                        lat = float(line.split(':', 1)[1].strip())
                    except (ValueError, IndexError):
                        continue
                        
                elif line.startswith('longitude:'):
                    try:
                        lon = float(line.split(':', 1)[1].strip())
                    except (ValueError, IndexError):
                        continue
                        
                elif line.startswith('location:'):
                    try:
                        location = line.split(':', 1)[1].strip()
                    except IndexError:
                        continue
            
            # Validate coordinates
            if lat is not None and lon is not None:
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    logger.info(f"LLM provided coordinates for {city}: {lat}, {lon}")
                    return lat, lon, location
                else:
                    logger.warning(f"LLM provided invalid coordinates: lat={lat}, lon={lon}")
            
            return None, None, f"LLM couldn't provide valid coordinates for '{city}'"
            
        except Exception as e:
            logger.error(f"LLM geocoding error for {city}: {e}")
            return None, None, f"LLM geocoding failed: {str(e)}"
    
    def _get_coordinates(self, city: str) -> tuple[Optional[float], Optional[float], str]:
        """
        Get coordinates with API first, LLM fallback.
        Returns (latitude, longitude, location_name)
        """
        # Try API first
        lat, lon, name = self._get_coordinates_from_api(city)
        if lat is not None and lon is not None:
            logger.debug(f"Used API geocoding for {city}")
            return lat, lon, name
        
        # Fallback to LLM
        logger.info(f"API geocoding failed for {city}, trying LLM fallback")
        lat, lon, name = self._get_coordinates_from_llm(city)
        if lat is not None and lon is not None:
            logger.info(f"Used LLM fallback geocoding for {city}")
            return lat, lon, f"{name} (LLM estimate)"
        
        # Both failed
        return None, None, f"Could not find coordinates for '{city}' via API or LLM, maybe you can supply them yourself? or maybe try looking for a city or a town nearby."
    
    def _execute(self, city: str, start_date: str, end_date: str) -> ToolResult:
        """Get weather data from Open-Meteo API."""
        
        # Validate dates
        is_valid, error_msg = self._validate_dates(start_date, end_date)
        if not is_valid:
            return ToolResult(
                success=False,
                error=error_msg,
                confidence="high"  # High confidence in validation errors
            )
        
        # Get coordinates
        lat, lon, location_name = self._get_coordinates(city)
        if lat is None or lon is None:
            return ToolResult(
                success=False,
                error=location_name,  # Contains error message
                confidence="high"
            )
        
        try:
            # Prepare API request
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min", 
                    "precipitation_probability_max",
                    "weather_code"
                ],
                "start_date": start_date,
                "end_date": end_date,
                "timezone": "auto"
            }
            
            # Make API request
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/forecast", params=params)
                response.raise_for_status()
                weather_data = response.json()
            
            # Process the response
            daily_data = weather_data.get("daily", {})
            
            if not daily_data:
                return ToolResult(
                    success=False,
                    error="No weather data received from API",
                    confidence="low"
                )
            
            # Format daily weather
            daily_weather = []
            dates = daily_data.get("time", [])
            max_temps = daily_data.get("temperature_2m_max", [])
            min_temps = daily_data.get("temperature_2m_min", [])
            precip_probs = daily_data.get("precipitation_probability_max", [])
            weather_codes = daily_data.get("weather_code", [])
            
            for i, date_str in enumerate(dates):
                daily_weather.append({
                    "date": date_str,
                    "tmax": max_temps[i] if i < len(max_temps) else None,
                    "tmin": min_temps[i] if i < len(min_temps) else None,
                    "precip_prob": precip_probs[i] if i < len(precip_probs) else 0,
                    "weather_code": weather_codes[i] if i < len(weather_codes) else None,
                    "conditions": self._weather_code_to_description(
                        weather_codes[i] if i < len(weather_codes) else None
                    )
                })
            
            # Generate summary
            avg_high = sum(d["tmax"] for d in daily_weather if d["tmax"]) / len(daily_weather)
            avg_low = sum(d["tmin"] for d in daily_weather if d["tmin"]) / len(daily_weather)
            max_precip = max(d["precip_prob"] for d in daily_weather)
            
            summary = f"Weather for {location_name}: "
            summary += f"Highs {avg_high:.1f}°C, lows {avg_low:.1f}°C. "
            
            if max_precip > 60:
                summary += "High chance of rain - pack waterproof gear."
            elif max_precip > 30:
                summary += "Some rain possible - consider bringing a light jacket."
            else:
                summary += "Generally dry conditions expected."
            
            return ToolResult(
                success=True,
                data={
                    "location": location_name,
                    "daily": daily_weather,
                    "summary": summary,
                    "avg_high": round(avg_high, 1),
                    "avg_low": round(avg_low, 1),
                    "max_precip_prob": max_precip
                },
                confidence="high"
            )
            
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error="Weather API request timed out",
                confidence="medium"
            )
        except httpx.HTTPError as e:
            return ToolResult(
                success=False,
                error=f"Weather API error: {str(e)}",
                confidence="low"
            )
        except Exception as e:
            logger.error(f"Unexpected error in weather tool: {e}")
            return ToolResult(
                success=False,
                error=f"Weather service unavailable: {str(e)}",
                confidence="low"
            )
    
    def _weather_code_to_description(self, code: Optional[int]) -> str:
        """Convert WMO weather code to description."""
        if code is None:
            return "Unknown"
        
        # WMO weather code mapping (simplified)
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with hail"
        }
        
        return weather_codes.get(code, f"Weather code {code}")


# Global weather tool instance
_weather_tool = WeatherTool()


def get_weather_tool() -> WeatherTool:
    """Get the weather tool instance."""
    return _weather_tool