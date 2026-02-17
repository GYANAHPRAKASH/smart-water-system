import unittest
import json
import asyncio
from app import create_app, db
from app.models import AIRequestLog

class Phase2TestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB for testing
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_calendar_script_block(self):
        """Test if base.html has the scripts block (static check)."""
        with open('app/templates/base.html', 'r') as f:
            content = f.read()
        self.assertIn('{% block scripts %}', content, "base.html missing {% block scripts %}")

    def test_api_predict_demand(self):
        """Test generic prediction API."""
        response = self.client.post('/api/predict_demand', json={'colony': 'Test Colony'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('predictions', data)
        
        # Verify DB Log
        with self.app.app_context():
            log = AIRequestLog.query.filter_by(endpoint='/api/predict_demand').first()
            self.assertIsNotNone(log, "AIRequestLog not created for predict_demand")
            self.assertIn('Test Colony', log.input_data)

    def test_api_analyze_complaint(self):
        """Test complaint analysis API."""
        response = self.client.post('/api/analyze_complaint', json={'description': 'Severe pipe burst'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['priority'], 'High')
        
        # Verify DB Log
        with self.app.app_context():
            log = AIRequestLog.query.filter_by(endpoint='/api/analyze_complaint').first()
            self.assertIsNotNone(log, "AIRequestLog not created for analyze_complaint")
            self.assertIn('Severe pipe burst', log.input_data)

if __name__ == '__main__':
    unittest.main()
