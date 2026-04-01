# pyre-ignore-all-errors
"""
AquaFlow AI Module — Water Demand Intelligence Engine
=====================================================
This module powers three AI/ML features:

1. analyze_complaint(description) — NLP keyword classifier → High/Medium/Low priority
2. predict_demand(colony)         — RandomForestRegressor trained on historical data
3. detect_anomalies(colony)       — Z-score statistical anomaly detection
4. generate_simulated_data(...)   — Seeds historical water usage data
5. generate_auto_schedule(...)    — AI-driven auto-scheduling

ML Pipeline for predict_demand:
  ┌─────────────────┐   ┌──────────────────────┐   ┌────────────────────────────┐
  │ MongoDB          │   │ Open-Meteo Forecast  │   │  scikit-learn              │
  │ water_usage (30d)│ + │ API (7-day weather)  │ → │  RandomForestRegressor     │
  │ (temp/rain used  │   │ (temp, precipitation │   │  Trained on 365d history   │
  │  as X features)  │   │  for Chennai)        │   │  Features: temp, rain,     │
  └─────────────────┘   └──────────────────────┘   │  day_of_week, month        │
                                                    └────────────────────────────┘
"""
from datetime import datetime, timedelta
import random
import statistics

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from . import mongo
from .weather_service import get_historical_weather, get_forecast

COLONIES = ["Anna Nagar", "Nungambakkam", "T. Nagar", "Alwarpet", "Gopalapuram"]

# ─────────────────────────────────────────────────────────────────
# 1. NLP-Based Complaint Priority Classifier
# ─────────────────────────────────────────────────────────────────

def analyze_complaint(description):
    """
    Classifies complaint severity using keyword-based NLP.

    The complaint text is tokenized and scanned for urgency signals:
    - HIGH: words indicating emergencies (burst, contaminated, no water...)
    - MEDIUM: words indicating degraded service (leakage, low pressure, smell...)
    - LOW: default, minor inconveniences

    Returns: 'High' | 'Medium' | 'Low'
    """
    description = description.lower()

    high_keywords = [
        'burst', 'urgent', 'contaminated', 'emergency',
        'severe', 'broken', 'no water', 'flooding', 'dangerous'
    ]
    medium_keywords = [
        'leakage', 'low pressure', 'dirty', 'smell',
        'cloudy', 'intermittent', 'irregular', 'weak'
    ]

    for word in high_keywords:
        if word in description:
            return 'High'

    for word in medium_keywords:
        if word in description:
            return 'Medium'

    return 'Low'


# ─────────────────────────────────────────────────────────────────
# 2. ML-Based Water Demand Predictor (RandomForestRegressor)
# ─────────────────────────────────────────────────────────────────

def _build_feature_vector(temp, rain, date_str):
    """
    Constructs the feature vector that the ML model uses for prediction.

    Features:
      [0] max_temp        — Daily max temperature °C (higher temp → higher demand)
      [1] precipitation   — Daily rainfall mm (rain > 5mm → demand drops ~20%)
      [2] day_of_week     — 0=Monday...6=Sunday (weekend patterns differ)
      [3] month           — 1-12 (captures seasonal effects: summer peak, monsoon dip)
      [4] is_summer       — 1 if Apr/May/Jun (Chennai heat peak), else 0
      [5] is_monsoon      — 1 if Oct/Nov/Dec (NE monsoon), else 0
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return [
        float(temp) if temp else 30.0,
        float(rain) if rain else 0.0,
        dt.weekday(),
        dt.month,
        1 if dt.month in [4, 5, 6] else 0,
        1 if dt.month in [10, 11, 12] else 0,
    ]


def _train_model(colony):
    """
    Trains a RandomForestRegressor on all available historical water usage data
    for the given colony, augmented with the actual weather that day.

    Training Data: MongoDB water_usage collection (up to 365 records per colony)
    Features (X): [max_temp, precipitation, day_of_week, month, is_summer, is_monsoon]
    Target  (y): amount_liters used that day

    Returns: (trained_model, scaler, r2_score, n_samples) or None if insufficient data.
    """
    records = list(mongo.db.water_usage.find({'colony': colony}).sort('date', 1))

    if len(records) < 30:
        return None, None, None, 0

    # Fetch actual historical weather to align with usage records
    days_needed = (datetime.today() - records[0]['date']).days + 1
    historical_weather = get_historical_weather(min(days_needed, 365))

    X, y = [], []
    for rec in records:
        date_str = rec['date'].strftime('%Y-%m-%d')
        w = historical_weather.get(date_str, {'temp': 30, 'rain': 0})
        features = _build_feature_vector(w.get('temp', 30), w.get('rain', 0), date_str)
        X.append(features)
        y.append(rec['amount_liters'])

    if len(X) < 20:
        return None, None, None, 0

    X_arr = np.array(X)
    y_arr = np.array(y)

    # Normalize features for better convergence
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_arr)

    # Split: 80% train, 20% hold-out test for scoring
    if len(X_arr) >= 50:
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_arr, test_size=0.2, random_state=42
        )
    else:
        X_train, X_test, y_train, y_test = X_scaled, X_scaled, y_arr, y_arr

    # Random Forest: 150 trees, captures non-linear patterns (temperature spikes,
    # monsoon effects, weekend usage changes)
    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=10,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1  # use all CPU cores
    )
    model.fit(X_train, y_train)

    r2 = round(model.score(X_test, y_test), 3)
    return model, scaler, r2, len(X)


def predict_demand(colony):
    """
    Predicts next 7 days of water demand for a colony using a trained ML model.

    Pipeline:
      1. Train RandomForestRegressor on colony's historical data (MongoDB)
      2. Fetch 7-day weather forecast from Open-Meteo API
      3. Build feature vectors for each forecast day
      4. Run predictions through the trained model
      5. Return list of {date, amount, weather, confidence, model_accuracy}

    Falls back to physics-based formula if insufficient training data.
    """
    model, scaler, r2, n_samples = _train_model(colony)
    forecast = get_forecast(7)

    # Fallback: not enough historical data yet
    if model is None or not forecast:
        recent = list(mongo.db.water_usage.find({'colony': colony}).sort('date', -1).limit(30))
        base = statistics.mean([r['amount_liters'] for r in recent]) if recent else 600000
        predictions = []
        for i, day in enumerate(forecast or []):
            temp = float(day.get('temp') or 30)
            rain = float(day.get('rain') or 0)
            t_factor = 1.0 + max(0.0, (temp - 30) * 0.02)
            r_factor = 0.8 if rain > 5.0 else 1.0
            predictions.append({
                'date': day['date'],
                'amount': int(base * t_factor * r_factor),
                'weather': f"{temp:.1f}°C, {rain:.1f}mm rain",
                'confidence': 'Formula',
                'model_accuracy': 'N/A (insufficient training data)',
                'feature_importance': {}
            })
        return predictions

    predictions = []
    today = datetime.today()

    for i, day in enumerate(forecast):
        temp = float(day.get('temp') or 30)
        rain = float(day.get('rain') or 0)
        date_str = day['date']

        features = _build_feature_vector(temp, rain, date_str)
        features_scaled = scaler.transform([features])
        predicted_val = model.predict(features_scaled)[0]

        # Clamp to realistic bounds (300k-1.2M litres)
        predicted_val = max(300_000, min(1_200_000, predicted_val))

        # Individual tree predictions for confidence interval
        tree_preds = np.array([tree.predict(features_scaled)[0] for tree in model.estimators_])
        std_dev = np.std(tree_preds)
        confidence_pct = max(0, min(100, int(100 - (std_dev / predicted_val * 100))))

        rain_label = "Heavy Rain 🌧️" if rain > 10 else ("Light Rain 🌦️" if rain > 2 else "Dry ☀️")

        predictions.append({
            'date': date_str,
            'amount': int(predicted_val),
            'weather': f"{temp:.1f}°C, {rain:.1f}mm ({rain_label})",
            'confidence': f"{confidence_pct}%",
            'model_accuracy': f"R² = {r2} (trained on {n_samples} days)",
            'std_dev': int(std_dev),
        })

    return predictions


# ─────────────────────────────────────────────────────────────────
# 3. Z-Score Anomaly Detection
# ─────────────────────────────────────────────────────────────────

def detect_anomalies(colony):
    """
    Detects statistically abnormal water usage days using Z-score analysis.

    Method:
      z = (value - mean) / stdev
      |z| > 2.0 → flagged as anomaly (outside 95% of normal distribution)

    Also attaches a contextual REASON and SUGGESTION based on month / direction.
    Returns last 10 anomalies for dashboard relevance.
    """
    data = list(mongo.db.water_usage.find({'colony': colony}).sort('date', 1))
    if not data or len(data) < 30:
        return []

    values = [d['amount_liters'] for d in data]
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)

    anomalies = []
    threshold = 2.0

    for record in data:
        amount = record['amount_liters']
        date_obj = record['date']
        z_score = (amount - mean) / stdev if stdev > 0 else 0

        if abs(z_score) > threshold:
            month = date_obj.month

            if z_score > 0:
                reason = "Unusually High Usage"
                suggestion = "Check for pipe leaks or unauthorized usage."
                if month in [4, 5, 6]:
                    reason += " (Summer Peak)"
                    suggestion = "Implement water rationing — summer demand spike detected."
                elif month in [1, 2]:
                    reason += " (Post-Harvest Season)"
                    suggestion = "Verify industrial/agricultural usage anomaly."
            else:
                reason = "Unusually Low Usage"
                suggestion = "Check meter functionality and supply valves."
                if month in [10, 11, 12]:
                    reason += " (NE Monsoon)"
                    suggestion = "Monitor reservoir levels for potential overflow."

            anomalies.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'amount': amount,
                'status': 'High' if z_score > 0 else 'Low',
                'z_score': round(z_score, 2),
                'reason': reason,
                'suggestion': suggestion
            })

    return anomalies[-10:]


# ─────────────────────────────────────────────────────────────────
# 4. Historical Data Generator (seeds the ML training set)
# ─────────────────────────────────────────────────────────────────

def generate_simulated_data(colony=None, days=365):
    """
    Seeds the MongoDB water_usage collection with realistic synthetic data
    based on actual Chennai weather (from Open-Meteo archive API).

    Without this data the ML model cannot train. Each record represents
    one day's total water consumption for a colony in litres.

    Demand model used for simulation:
      usage = base * temp_factor * rain_factor * noise
      - temp_factor: +2% per degree above 30°C
      - rain_factor: -20% if rainfall > 5mm
      - noise: ±5% random, 1% chance of spike anomaly (+30%)
    """
    target_colonies = [colony] if colony else COLONIES

    print("Fetching historical weather for data generation...")
    weather_history = get_historical_weather(days)

    today = datetime.today()
    today_dt = datetime(today.year, today.month, today.day)

    base_usages = {
        "Anna Nagar":    650_000,
        "Nungambakkam":  550_000,
        "T. Nagar":      700_000,
        "Alwarpet":      500_000,
        "Gopalapuram":   480_000,
    }

    for col in target_colonies:
        print(f"Generating data for {col}...")
        base = base_usages.get(col, 600_000)

        if mongo.db.water_usage.find_one({'colony': col, 'date': today_dt}):
            print(f"  → Data exists for today, skipping {col}")
            continue

        records = []
        for i in range(days):
            date_obj = today_dt - timedelta(days=days - i)
            date_str = date_obj.strftime('%Y-%m-%d')

            w = weather_history.get(date_str, {'temp': 30, 'rain': 0})
            temp = float(w.get('temp') or 30)
            rain = float(w.get('rain') or 0)

            temp_factor = 1.0 + max(0.0, (temp - 30) * 0.02)
            rain_factor = 0.8 if rain > 5.0 else 1.0
            usage = base * temp_factor * rain_factor
            usage *= random.uniform(0.95, 1.05)

            if random.random() < 0.01:
                usage *= 1.3  # spike: burst pipe / massive leak anomaly

            records.append({
                'colony': col,
                'date': date_obj,
                'amount_liters': int(usage)
            })

        if records:
            mongo.db.water_usage.insert_many(records)

    print("Data generation complete.")


# ─────────────────────────────────────────────────────────────────
# 5. AI Auto-Scheduler
# ─────────────────────────────────────────────────────────────────

def generate_auto_schedule(colony):
    """
    Uses the ML demand predictor to automatically schedule the next 30 days.
    Days where predicted demand exceeds safe capacity → Shutdown/Maintenance.
    """
    today = datetime.today()
    mongo.db.schedules.delete_many({'colony': colony, 'date_time': {'$gte': today}})

    MAX_CAPACITY = 800_000
    forecast = get_forecast(7)
    model, scaler, r2, n_samples = _train_model(colony)

    new_schedules = []
    for i in range(30):
        future_date = today + timedelta(days=i + 1)
        date_str = future_date.strftime('%Y-%m-%d')

        day_weather = forecast[i % 7] if forecast and i < 7 else {'temp': 30, 'rain': 0}
        temp = float(day_weather.get('temp') or 30)
        rain = float(day_weather.get('rain') or 0)

        # Use ML model if available, else formula
        if model:
            features_scaled = scaler.transform([_build_feature_vector(temp, rain, date_str)])
            predicted_val = model.predict(features_scaled)[0]
        else:
            t_factor = 1.0 + max(0.0, (temp - 30) * 0.02)
            r_factor = 0.8 if rain > 5.0 else 1.0
            recent = list(mongo.db.water_usage.find({'colony': colony}).sort('date', -1).limit(30))
            base = statistics.mean([r['amount_liters'] for r in recent]) if recent else 600_000
            predicted_val = base * t_factor * r_factor * random.uniform(0.95, 1.05)

        action = "Supply"
        notes = f"AI-scheduled supply. Predicted: {int(predicted_val):,} L (R²={r2})"

        if predicted_val > MAX_CAPACITY:
            action = "Shutdown"
            notes = f"Predicted demand ({int(predicted_val):,} L) exceeds safe capacity. Maintenance required."
        elif random.random() < 0.05:
            action = "Shutdown"
            notes = "Scheduled valve maintenance (AI-triggered 5% maintenance probability)."

        new_schedules.append({
            'colony': colony,
            'date_time': future_date,
            'action': action,
            'notes': notes
        })

    if new_schedules:
        mongo.db.schedules.insert_many(new_schedules)
