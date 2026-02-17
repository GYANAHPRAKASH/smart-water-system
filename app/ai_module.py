from datetime import datetime, timedelta
import random
import statistics
from . import db
from .models import WaterUsage
from .weather_service import get_historical_weather, get_forecast

COLONIES = ["Anna Nagar", "Nungambakkam", "T. Nagar", "Alwarpet", "Gopalapuram"]

def analyze_complaint(description):
    """
    Analyzes the complaint description and returns a priority.
    Keywords based:
    - High: burst, urgent, contaminated, emergency, severe, broken pipe
    - Medium: leakage, low pressure, dirty, smell
    - Low: slow, trickle, noise
    """
    description = description.lower()
    
    high_keywords = ['burst', 'urgent', 'contaminated', 'emergency', 'severe', 'broken', 'no water']
    medium_keywords = ['leakage', 'low pressure', 'dirty', 'smell', 'cloudy']
    
    for word in high_keywords:
        if word in description:
            return 'High'
            
    for word in medium_keywords:
        if word in description:
            return 'Medium'
            
    return 'Low'

def generate_simulated_data(colony=None, days=365):
    """
    Generates simulated water usage data for the last 'days' based on ACTUAL Chennai weather.
    If colony is None, generates for ALL colonies.
    """
    target_colonies = [colony] if colony else COLONIES
    
    # Check if we already have data to avoid duplicate generation if called blindly
    # But for this task, we usually want to ensure we populate if empty
    
    print("Fetching historical weather for simulation...")
    weather_history = get_historical_weather(days)
    
    today = datetime.today().date()
    
    # Base usage per colony (simulating different sizes)
    base_usages = {
        "Anna Nagar": 8000,
        "Nungambakkam": 6500,
        "T. Nagar": 9000, # Busy area
        "Alwarpet": 5500,
        "Gopalapuram": 5000
    }

    for col in target_colonies:
        print(f"Generating data for {col}...")
        base = base_usages.get(col, 6000)
        
        # Check if data exists for today to prevent full overwrite overlap if running daily
        # For simplicity, we'll check just one record
        if WaterUsage.query.filter_by(colony=col, date=today).first():
            continue

        for i in range(days):
            date_obj = today - timedelta(days=days-i)
            date_str = date_obj.strftime("%Y-%m-%d")
            
            weather = weather_history.get(date_str, {'temp': 30, 'rain': 0})
            temp = weather['temp'] if weather['temp'] else 30
            rain = weather['rain'] if weather['rain'] else 0
            
            # Demand Logic:
            # 1. Temperature: +2% per degree above 30C
            # 2. Rain: -20% if rain > 5mm (Monsoon/Storm)
            
            temp_factor = 1.0 + max(0, (temp - 30) * 0.02)
            rain_factor = 0.8 if rain > 5.0 else 1.0
            
            usage = base * temp_factor * rain_factor
            
            # Add random noise (+/- 5%)
            usage *= random.uniform(0.95, 1.05)
            
            # Inject Anomalies (randomly 1% chance)
            if random.random() < 0.01:
                usage *= 1.5 # Pipe burst or massive leak
                
            record = WaterUsage(colony=col, date=date_obj, amount_liters=int(usage))
            db.session.add(record)
            
    db.session.commit()
    print("Data generation complete.")

def predict_demand(colony):
    """
    Predicts next 7 days demand using WEATHER FORECAST.
    """
    # Get 7-day forecast
    forecast = get_forecast(7)
    
    # Get recent average base usage (last 30 days) to baseline
    recent_data = WaterUsage.query.filter_by(colony=colony).order_by(WaterUsage.date.desc()).limit(30).all()
    if not recent_data:
        base_usage = 6000
    else:
        base_usage = statistics.mean([d.amount_liters for d in recent_data])
        
    predictions = []
    
    for day_weather in forecast:
        temp = day_weather['temp'] if day_weather['temp'] else 30
        rain = day_weather['rain'] if day_weather['rain'] else 0
        
        # Apply same logic as generation
        temp_factor = 1.0 + max(0, (temp - 30) * 0.02)
        rain_factor = 0.8 if rain > 5.0 else 1.0
        
        predicted_val = base_usage * temp_factor * rain_factor
        
        predictions.append({
            'date': day_weather['date'],
            'amount': int(predicted_val),
            'weather': f"{temp}°C, {rain}mm"
        })
        
    return predictions

def detect_anomalies(colony):
    """
    Detects anomalies and provides REASONS based on context.
    """
    data = WaterUsage.query.filter_by(colony=colony).order_by(WaterUsage.date.asc()).all()
    if not data or len(data) < 30:
        return []
        
    values = [d.amount_liters for d in data]
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    
    anomalies = []
    threshold = 2 # Z-score
    
    for record in data:
        z_score = (record.amount_liters - mean) / stdev if stdev > 0 else 0
        if abs(z_score) > threshold:
            
            # Determine Reason
            reason = "Unknown"
            month = record.date.month
            
            if z_score > 0:
                reason = "Unusually High Usage"
                # Check Month for context
                if month in [4, 5, 6]: # April, May, June
                    reason += " (Summer Peak?)"
            else:
                reason = "Unusually Low Usage"
                if month in [10, 11, 12]: # Oct, Nov, Dec (Chennai Monsoon)
                    reason += " (Heavy Rains?)"
            
            anomalies.append({
                'date': record.date.strftime('%Y-%m-%d'),
                'amount': record.amount_liters,
                'status': 'High' if z_score > 0 else 'Low',
                'reason': reason
            })
            
    # Return only recent anomalies (last 30 days) for dashboard relevance
    return anomalies[-10:]
