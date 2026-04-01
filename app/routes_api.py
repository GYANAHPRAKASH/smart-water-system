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
    ML endpoint: predicts 7-day water demand for a given colony.
    Returns clean JSON error on any failure — never crashes.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON body.'}), 400

        colony = data.get('colony', '').strip()
        if not colony:
            return jsonify({'status': 'error', 'message': 'Colony name is required.'}), 400

        predictions = predict_demand(colony)

        # Log to DB (non-blocking — failure here should not break the response)
        try:
            mongo.db.ai_logs.insert_one({
                'endpoint': '/api/predict_demand',
                'input_data': json.dumps(data),
                'output_data': json.dumps(predictions),
                'timestamp': datetime.utcnow()
            })
        except Exception:
            pass  # DB log failure should never affect the response

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

    except Exception as e:
        # Return a structured error — never expose internal traceback to client
        return jsonify({
            'status': 'error',
            'message': 'Prediction service temporarily unavailable. Please try again.',
            'detail': str(e)
        }), 500


@api.route('/api/analyze_complaint', methods=['POST'])
def api_analyze_complaint():
    """
    NLP endpoint: classifies complaint description into High/Medium/Low priority.
    Returns clean JSON error on any failure — never crashes.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON body.'}), 400

        description = data.get('description', '').strip()
        if not description:
            return jsonify({'status': 'error', 'message': 'Description is required.'}), 400

        if len(description) > 2000:
            return jsonify({'status': 'error', 'message': 'Description too long (max 2000 chars).'}), 400

        priority = analyze_complaint(description)

        # Log to DB (non-blocking)
        try:
            mongo.db.ai_logs.insert_one({
                'endpoint': '/api/analyze_complaint',
                'input_data': json.dumps(data),
                'output_data': json.dumps({'priority': priority}),
                'timestamp': datetime.utcnow()
            })
        except Exception:
            pass

        return jsonify({
            'status': 'success',
            'priority': priority,
            'original_text': description
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Analysis service temporarily unavailable.',
            'detail': str(e)
        }), 500
