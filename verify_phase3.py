import unittest
from app import create_app, db
from app.models import WaterUsage
from app.weather_service import get_historical_weather
from app.routes_admin import predict_demand, detect_anomalies

class DataEnhancementTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_weather_service(self):
        """Test if weather service can fetch data."""
        print("Testing Weather Service...")
        weather = get_historical_weather(days=5)
        self.assertTrue(len(weather) > 0, "Failed to fetch historical weather")
        print("Weather fetch successful.")

    def test_data_population(self):
        """Test if data exists for new colonies."""
        print("Testing Data Population...")
        colonies = ["Anna Nagar", "Nungambakkam"]
        for col in colonies:
            count = WaterUsage.query.filter_by(colony=col).count()
            print(f"{col} record count: {count}")
            self.assertTrue(count > 0, f"No data found for {col}")

    def test_anomaly_reasons(self):
        """Test if anomalies have reasons."""
        print("Testing Anomaly Logic...")
        anomalies = detect_anomalies("Anna Nagar")
        if anomalies:
            self.assertIn('reason', anomalies[0], "Anomaly missing 'reason' field")
            print(f"Sample Anomaly Reason: {anomalies[0]['reason']}")
        else:
            print("No anomalies detected to test reasons (this is possible if data is too clean).")

if __name__ == '__main__':
    unittest.main()
