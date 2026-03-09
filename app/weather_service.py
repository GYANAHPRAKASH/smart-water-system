# pyre-ignore-all-errors
import requests
import datetime

# Chennai Coordinates
LAT = 13.0827
LON = 80.2707

def get_historical_weather(days=365):
    """
    Fetches historical weather (daily max temp and precipitation sum) for Chennai.
    Returns a dictionary keyed by date string 'YYYY-MM-DD'.
    """
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": ["temperature_2m_max", "precipitation_sum"],
        "timezone": "Asia/Kolkata"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        weather_map = {}
        if 'daily' in data:
            daily = data['daily']
            for i, date in enumerate(daily['time']):
                weather_map[date] = {
                    'temp': daily['temperature_2m_max'][i],
                    'rain': daily['precipitation_sum'][i]
                }
        return weather_map
    except Exception as e:
        print(f"Error fetching historical weather: {e}")
        return {}

def get_forecast(days=7):
    """
    Fetches 7-day forecast for Chennai.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": ["temperature_2m_max", "precipitation_sum"],
        "timezone": "Asia/Kolkata",
        "forecast_days": days
    }
    
    try:
        response = requests.get(url, params=params)
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
        return forecast
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        return []
