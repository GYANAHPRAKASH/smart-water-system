# pyre-ignore-all-errors
from flask import Blueprint, jsonify, request
import json
from datetime import datetime
from app import mongo
from app.ai_module import analyze_complaint, predict_demand

api = Blueprint('api', __name__)

@api.route('/api/predict_demand', methods=['POST'])
def api_predict_demand():
    """
    API endpoint to predict water demand.
    Runs synchronously — compatible with standard gunicorn workers.
    """
    data = request.get_json()
    colony = data.get('colony', 'General')

    predictions = predict_demand(colony)

    # Log to DB
    log = {
        'endpoint': '/api/predict_demand',
        'input_data': json.dumps(data),
        'output_data': json.dumps(predictions),
        'timestamp': datetime.utcnow()
    }
    mongo.db.ai_logs.insert_one(log)

    # Extract model metadata from first prediction if available
    model_info = {}
    if predictions:
        first = predictions[0]
        model_info = {
            'model_type': 'RandomForestRegressor (scikit-learn)',
            'accuracy': first.get('model_accuracy', 'N/A'),
            'features': ['max_temp', 'precipitation', 'day_of_week', 'month', 'is_summer', 'is_monsoon'],
            'weather_api': 'Open-Meteo Forecast API (open-meteo.com)',
        }

    return jsonify({
        'status': 'success',
        'colony': colony,
        'predictions': predictions,
        'model_info': model_info,
        'message': 'ML model prediction completed successfully.'
    })

@api.route('/api/analyze_complaint', methods=['POST'])
def api_analyze_complaint():
    """
    API endpoint to analyze complaint priority.
    Runs synchronously — compatible with standard gunicorn workers.
    """
    data = request.get_json()
    description = data.get('description', '')

    priority = analyze_complaint(description)

    # Log to DB
    log = {
        'endpoint': '/api/analyze_complaint',
        'input_data': json.dumps(data),
        'output_data': json.dumps({'priority': priority}),
        'timestamp': datetime.utcnow()
    }
    mongo.db.ai_logs.insert_one(log)

    return jsonify({
        'status': 'success',
        'priority': priority,
        'original_text': description
    })
