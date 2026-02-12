import random
import statistics
from datetime import datetime, timedelta
from . import db
from .models import WaterUsage

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

def generate_simulated_data(colony, days=30):
    """
    Generates simulated water usage data for the last 'days'.
    Normal usage is around 5000-7000 liters.
    Adds random spikes for anomalies.
    """
    # Check if data already exists to avoid duplication
    if WaterUsage.query.filter_by(colony=colony).first():
        return

    today = datetime.today().date()
    base_usage = 6000
    
    for i in range(days):
        date = today - timedelta(days=days-i)
        # Random fluctuation
        fluctuation = random.randint(-500, 500)
        usage = base_usage + fluctuation
        
        # Inject Anomaly (Weekly)
        if i % 10 == 0: 
            usage += random.randint(2000, 4000) # Big spike
            
        record = WaterUsage(colony=colony, date=date, amount_liters=usage)
        db.session.add(record)
    
    db.session.commit()

def predict_demand(colony):
    """
    Predicts next 7 days demand using simple moving average of last 30 days.
    """
    data = WaterUsage.query.filter_by(colony=colony).order_by(WaterUsage.date.asc()).all()
    if not data:
        return []
        
    usage_values = [d.amount_liters for d in data]
    avg_usage = statistics.mean(usage_values)
    
    predictions = []
    today = datetime.today().date()
    
    for i in range(1, 8):
        future_date = today + timedelta(days=i)
        # Simple prediction: Average + small random growth factor
        predicted_val = avg_usage * random.uniform(0.95, 1.05)
        predictions.append({
            'date': future_date.strftime('%Y-%m-%d'),
            'amount': int(predicted_val)
        })
        
    return predictions

def detect_anomalies(colony):
    """
    Detects anomalies using Z-Score (Mean +/- 2 Std Dev).
    Returns list of anomaly records.
    """
    data = WaterUsage.query.filter_by(colony=colony).order_by(WaterUsage.date.asc()).all()
    if not data or len(data) < 5:
        return []
        
    values = [d.amount_liters for d in data]
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    
    anomalies = []
    threshold = 2 # Z-score threshold
    
    for record in data:
        z_score = (record.amount_liters - mean) / stdev if stdev > 0 else 0
        if abs(z_score) > threshold:
            anomalies.append({
                'date': record.date.strftime('%Y-%m-%d'),
                'amount': record.amount_liters,
                'status': 'High Usage' if z_score > 0 else 'Low Usage'
            })
            
    return anomalies
