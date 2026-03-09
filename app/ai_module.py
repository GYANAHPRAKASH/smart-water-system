# pyre-ignore-all-errors
from datetime import datetime, timedelta
import random
import statistics
from . import mongo
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
    
    today = datetime.today()
    today_dt = datetime(today.year, today.month, today.day)
    
    # Base usage per colony (simulating different sizes) -> UPDATED to 5-7 Lakhs
    base_usages = {
        "Anna Nagar": 650000,
        "Nungambakkam": 550000,
        "T. Nagar": 700000, # Busy area
        "Alwarpet": 500000,
        "Gopalapuram": 480000
    }

    for col in target_colonies:
        print(f"Generating data for {col}...")
        base = base_usages.get(col, 600000)
        
        # Check if data exists for today to prevent full overwrite overlap if running daily
        if mongo.db.water_usage.find_one({'colony': col, 'date': today_dt}):
            continue

        records = []
        for i in range(days):
            date_obj = today_dt - timedelta(days=days-i)
            date_str = date_obj.strftime("%Y-%m-%d")
            
            weather = weather_history.get(date_str, {'temp': 30, 'rain': 0})
            temp = weather['temp'] if weather['temp'] else 30
            rain = weather['rain'] if weather['rain'] else 0
            
            # Demand Logic:
            # 1. Temperature: +2% per degree above 30C
            # 2. Rain: -20% if rain > 5mm (Monsoon/Storm)
            
            temp_factor = 1.0 + max(0.0, float(temp - 30) * 0.02)
            rain_factor = 0.8 if rain > 5.0 else 1.0
            
            usage = base * temp_factor * rain_factor
            
            # Add random noise (+/- 5%)
            usage *= random.uniform(0.95, 1.05)
            
            # Inject Anomalies (randomly 1% chance)
            if random.random() < 0.01:
                usage *= 1.3 # Pipe burst or massive leak
                
            records.append({
                'colony': col,
                'date': date_obj,
                'amount_liters': int(usage)
            })
            
        if records:
            mongo.db.water_usage.insert_many(records)
            
    print("Data generation complete.")

def predict_demand(colony):
    """
    Predicts next 7 days demand using WEATHER FORECAST.
    """
    # Get 7-day forecast
    forecast = get_forecast(7)
    
    # Get recent average base usage (last 30 days) to baseline
    recent_data = list(mongo.db.water_usage.find({'colony': colony}).sort('date', -1).limit(30))
    if not recent_data:
        base_usage = 600000
    else:
        base_usage = statistics.mean([d['amount_liters'] for d in recent_data])
        
    predictions = []
    
    for day_weather in forecast:
        temp = day_weather['temp'] if day_weather['temp'] else 30
        rain = day_weather['rain'] if day_weather['rain'] else 0
        
        # Apply same logic as generation
        temp_factor = 1.0 + max(0.0, float(temp - 30) * 0.02)
        rain_factor = 0.8 if float(rain) > 5.0 else 1.0
        
        predicted_val = float(base_usage) * temp_factor * rain_factor
        
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
    data = list(mongo.db.water_usage.find({'colony': colony}).sort('date', 1))
    if not data or len(data) < 30:
        return []
        
    values = [d['amount_liters'] for d in data]
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    
    anomalies: list = []
    threshold = 2 # Z-score
    
    for record in data:
        amount = record['amount_liters']
        date_obj = record['date']
        
        z_score = (amount - mean) / stdev if stdev > 0 else 0
        if abs(z_score) > threshold:
            
            # Determine Reason & Suggestion
            reason = "Unknown"
            suggestion = "Investigate usage patterns."
            month = date_obj.month
            
            if z_score > 0:
                reason = "Unusually High Usage"
                suggestion = "Check for pipe leaks or unauthorized usage."
                # Check Month for context
                if month in [4, 5, 6]: # April, May, June
                    reason += " (Summer Peak?)"
                    suggestion = "Implement water rationing if capacity is low."
            else:
                reason = "Unusually Low Usage"
                suggestion = "Check meter functionality."
                if month in [10, 11, 12]: # Oct, Nov, Dec (Chennai Monsoon)
                    reason += " (Heavy Rains?)"
                    suggestion = "Monitor reservoir levels for overflow."
            
            anomalies.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'amount': amount,
                'status': 'High' if z_score > 0 else 'Low',
                'reason': reason,
                'suggestion': suggestion
            })
            
    # Return only recent anomalies (last 30 days) for dashboard relevance
    return anomalies[-10:]

def generate_auto_schedule(colony):
    """
    Automatically generates water supply schedule for the NEXT 30 days.
    Defaults to Supply (Green).
    """
    # Clear future schedules for this colony to avoid duplicates
    today = datetime.today()
    mongo.db.schedules.delete_many({'colony': colony, 'date_time': {'$gte': today}})
    
    # Safe Capacity
    MAX_CAPACITY = 800000 
    
    # Get Forecast
    recent_data = list(mongo.db.water_usage.find({'colony': colony}).sort('date', -1).limit(30))
    if not recent_data:
        base_usage = 600000
    else:
        base_usage = statistics.mean([d['amount_liters'] for d in recent_data])

    forecast = get_forecast(7) 
    
    new_schedules = []
    for i in range(30):
        future_date = today + timedelta(days=i+1)
        
        # Predict usage
        day_weather = forecast[i % 7] if i < 7 else {'temp': 30, 'rain': 0}
        temp = day_weather['temp'] if day_weather.get('temp') else 30
        
        temp_factor = 1.0 + max(0.0, float(temp - 30) * 0.02)
        predicted_val = float(base_usage) * temp_factor * random.uniform(0.95, 1.05)
        
        action = "Supply"
        notes = "Auto-scheduled supply."
        
        # Logic for Shutdown
        if predicted_val > MAX_CAPACITY:
            action = "Shutdown"
            notes = "Predicted Demand exceeds capacity. Maintenance required."
        elif random.random() < 0.05: # 5% random maintenance
            action = "Shutdown"
            notes = "Scheduled Valve Maintenance."
            
        new_schedules.append({
            'colony': colony,
            'date_time': future_date,
            'action': action,
            'notes': notes
        })
        
    if new_schedules:
        mongo.db.schedules.insert_many(new_schedules)
