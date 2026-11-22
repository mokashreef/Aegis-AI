"""
Weather Forecast - Community Plugin Handler for Aegis AI.
Demonstrates structured return format and offline fallback.
"""

from typing import Any, Dict


def get_weather(city: str, **kwargs: Any) -> Dict[str, Any]:
    """Returns weather information for the specified city."""
    city_clean = city.strip()
    if not city_clean:
        return {
            "success": False,
            "error": "City name cannot be empty.",
        }

    # Deterministic sample weather mapping for offline reliability
    WEATHER_DATABASE = {
        "amman": {"condition": "مشمس ومعتدل (Sunny)", "temp_c": 22, "humidity": "45%", "wind_kmh": 14},
        "عمان": {"condition": "مشمس ومعتدل (Sunny)", "temp_c": 22, "humidity": "45%", "wind_kmh": 14},
        "riyadh": {"condition": "صافٍ ودافئ (Clear)", "temp_c": 31, "humidity": "18%", "wind_kmh": 11},
        "الرياض": {"condition": "صافٍ ودافئ (Clear)", "temp_c": 31, "humidity": "18%", "wind_kmh": 11},
        "london": {"condition": "غائم جزئياً (Partly Cloudy)", "temp_c": 16, "humidity": "72%", "wind_kmh": 19},
        "لندن": {"condition": "غائم جزئياً (Partly Cloudy)", "temp_c": 16, "humidity": "72%", "wind_kmh": 19},
        "new york": {"condition": "صافٍ ومنعش (Breezy)", "temp_c": 18, "humidity": "50%", "wind_kmh": 16},
        "نيويورك": {"condition": "صافٍ ومنعش (Breezy)", "temp_c": 18, "humidity": "50%", "wind_kmh": 16},
    }

    low = city_clean.lower()
    data = WEATHER_DATABASE.get(low, {
        "condition": "طقس لطيف ومعتدل (Pleasant)",
        "temp_c": 24,
        "humidity": "50%",
        "wind_kmh": 12,
    })

    return {
        "success": True,
        "city": city_clean,
        "temperature_celsius": data["temp_c"],
        "condition": data["condition"],
        "humidity": data["humidity"],
        "wind_kmh": data["wind_kmh"],
        "message": f"الطقس في {city_clean}: {data['condition']}، درجة الحرارة: {data['temp_c']}°C.",
    }
