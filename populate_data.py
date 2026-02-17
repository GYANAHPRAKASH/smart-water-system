from app import create_app, db
from app.models import WaterUsage
from app.ai_module import generate_simulated_data

app = create_app()

with app.app_context():
    print("Clearing old water usage data...")
    # Clean up old data to avoid mixing simulated random data with "real" weather data
    try:
        num_deleted = db.session.query(WaterUsage).delete()
        db.session.commit()
        print(f"Deleted {num_deleted} old records.")
    except Exception as e:
        print(f"Error clearing data: {e}")
        db.session.rollback()

    print("Generating new realistic data for Chennai colonies...")
    # Generate 365 days of data for all colonies
    generate_simulated_data(days=365)
    
    print("Database population complete!")
