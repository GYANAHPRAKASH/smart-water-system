# pyre-ignore-all-errors
import requests
import datetime

# Chennai Coordinates
LAT = 13.0827
LON = 80.2707

# ─────────────────────────────────────────────────────────────────
# In-Memory TTL Cache (avoids re-fetching on every request)
# Historical weather: valid for 24 hours (data doesn't change)
# Forecast: valid for 1 hour (updates daily)
# ─────────────────────────────────────────────────────────────────
_historical_cache = {'data': None, 'fetched_at': None}
_forecast_cache   = {'data': None, 'fetched_at': None}

HISTORICAL_TTL_HOURS = 24
FORECAST_TTL_HOURS   = 1


def _cache_valid(cache, ttl_hours):
    if cache['data'] is None or cache['fetched_at'] is None:
        return False
    age = (datetime.datetime.utcnow() - cache['fetched_at']).total_seconds() / 3600
    return age < ttl_hours


def get_historical_weather(days=365):
    """
    Fetches historical weather (daily max temp + precipitation) for Chennai.
    Returns a dict keyed by 'YYYY-MM-DD'.
    Cached in memory for 24 hours — only one HTTP call per server restart.
    """
    global _historical_cache
    if _cache_valid(_historical_cache, HISTORICAL_TTL_HOURS):
        return _historical_cache['data']

    end_date   = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   LAT,
        "longitude":  LON,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date":   end_date.strftime("%Y-%m-%d"),
        "daily":      ["temperature_2m_max", "precipitation_sum"],
        "timezone":   "Asia/Kolkata"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        weather_map = {}
        if 'daily' in data:
            daily = data['daily']
            for i, date in enumerate(daily['time']):
                weather_map[date] = {
                    'temp': daily['temperature_2m_max'][i],
                    'rain': daily['precipitation_sum'][i]
                }
        _historical_cache = {'data': weather_map, 'fetched_at': datetime.datetime.utcnow()}
        return weather_map
    except Exception as e:
        print(f"[AquaFlow] Error fetching historical weather: {e}")
        # Return cached data if available even if stale, else empty
        return _historical_cache['data'] or {}


def get_forecast(days=7):
    """
    Fetches 7-day forecast for Chennai.
    Cached in memory for 1 hour — only one HTTP call per hour.
    """
    global _forecast_cache
    if _cache_valid(_forecast_cache, FORECAST_TTL_HOURS):
        return _forecast_cache['data']

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":     LAT,
        "longitude":    LON,
        "daily":        ["temperature_2m_max", "precipitation_sum"],
        "timezone":     "Asia/Kolkata",
        "forecast_days": days
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        forecast = []
        if 'daily' in data:
            daily = data['daily']
            for i, date in enumerate(daily['time']):
                forecast.append({
                    'date': date,
                    'temp': daily['temperature_2m_max'][i],
                    'rain': daily['precipitation_sum'][i]
                })
        _forecast_cache = {'data': forecast, 'fetched_at': datetime.datetime.utcnow()}
        return forecast
    except Exception as e:
        print(f"[AquaFlow] Error fetching forecast: {e}")
        if _forecast_cache.get('data'):
            return _forecast_cache['data']
            
        # Guarantee 7-day fallback so UI never breaks
        fallback = []
        for i in range(days):
            dt = (datetime.date.today() + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            fallback.append({'date': dt, 'temp': 34.0, 'rain': 0.0})
        return fallback
