# pyre-ignore-all-errors
from flask import Blueprint, jsonify, request
import asyncio
import random
from datetime import datetime
from app import mongo
from app.ai_module import analyze_complaint, predict_demand

api = Blueprint('api', __name__)

@api.route('/api/predict_demand', methods=['POST'])
async def api_predict_demand():
    """
    Async API endpoint to predict water demand.
    Simulates a long-running AI process using asyncio.sleep.
    """
    data = request.get_json()
    colony = data.get('colony', 'General')
    
    # Simulate heavy AI processing (Latency & Async Handling)
    await asyncio.sleep(2) 
    
    predictions = predict_demand(colony)
    
    # Log to DB
    import json
    log = {
        'endpoint': '/api/predict_demand',
        'input_data': json.dumps(data),
        'output_data': json.dumps(predictions),
        'timestamp': datetime.utcnow()
    }
    mongo.db.ai_logs.insert_one(log)
    
    return jsonify({
        'status': 'success',
        'colony': colony,
        'predictions': predictions,
        'message': 'AI processing completed successfully.'
    })

@api.route('/api/analyze_complaint', methods=['POST'])
async def api_analyze_complaint():
    """
    Async API endpoint to analyze complaint priority.
    """
    data = request.get_json()
    description = data.get('description', '')
    
    # Simulate processing
    await asyncio.sleep(1)
    
    priority = analyze_complaint(description)
    
    # Log to DB
    import json
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
