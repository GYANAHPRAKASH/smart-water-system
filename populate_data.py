from app import create_app, mongo
from app.models import User
from app.ai_module import generate_simulated_data

app = create_app()

with app.app_context():
    print("Clearing old water usage data...")
    # Clean up old data to avoid mixing simulated random data with "real" weather data
    try:
        result = mongo.db.water_usage.delete_many({})
        print(f"Deleted {result.deleted_count} old records.")
    except Exception as e:
        print(f"Error clearing data: {e}")

    print("Generating new realistic data for Chennai colonies...")
    # Generate 365 days of data for all colonies
    generate_simulated_data(days=365)
    
    print("Auto-scheduling water supply for next 30 days...")
    from app.ai_module import generate_auto_schedule, COLONIES
    for col in COLONIES:
        generate_auto_schedule(col)
    
    print("Cleaning up invalid users...")
    valid_colonies = ["Anna Nagar", "Nungambakkam", "T. Nagar", "Alwarpet", "Gopalapuram"]
    result = mongo.db.users.delete_many({'colony': {'$nin': valid_colonies}, 'role': {'$ne': 'admin'}})
    print(f"Deleted {result.deleted_count} invalid users.")
    
    # Generate Dummy Users
    print("Generating dummy users for demo...")
    dummy_users = [
        {"username": "arun_anna", "first": "Arun", "last": "Kumar", "colony": "Anna Nagar", "door": "A-101"},
        {"username": "priya_anna", "first": "Priya", "last": "Rajan", "colony": "Anna Nagar", "door": "A-102"},
        {"username": "ravi_nung", "first": "Ravi", "last": "Shankar", "colony": "Nungambakkam", "door": "N-201"},
        {"username": "deepa_tng", "first": "Deepa", "last": "Krishnan", "colony": "T. Nagar", "door": "T-301"},
        {"username": "balaji_alw", "first": "Balaji", "last": "Srinivasan", "colony": "Alwarpet", "door": "AL-401"},
        {"username": "karthik_gop", "first": "Karthik", "last": "Raja", "colony": "Gopalapuram", "door": "G-501"}
    ]
    
    for d in dummy_users:
        if not mongo.db.users.find_one({'username': d['username']}):
            u_data = {
                'username': d['username'],
                'first_name': d['first'],
                'last_name': d['last'],
                'phone': "9876543210",
                'door_no': d['door'],
                'colony': d['colony'],
                'role': 'user',
                'status': 'approved',
                'password_hash': User.generate_hash("password123"),
                'credits': 0
            }
            mongo.db.users.insert_one(u_data)
            print(f"Added user: {d['username']}")

    print("Database population complete!")
