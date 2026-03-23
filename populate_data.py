# pyre-ignore-all-errors
from app import create_app, mongo
from app.models import User
from app.ai_module import generate_simulated_data

app = create_app()

with app.app_context():
    print("Clearing old water usage data...")
    try:
        result = mongo.db.water_usage.delete_many({})
        print(f"Deleted {result.deleted_count} old records.")
    except Exception as e:
        print(f"Error clearing data: {e}")

    print("Generating new realistic data for Chennai colonies...")
    generate_simulated_data(days=365)
    
    print("Auto-scheduling water supply for next 30 days...")
    from app.ai_module import generate_auto_schedule, COLONIES
    for col in COLONIES:
        generate_auto_schedule(col)
    
    print("Cleaning up invalid users...")
    valid_colonies = ["Anna Nagar", "Nungambakkam", "T. Nagar", "Alwarpet", "Gopalapuram"]
    result = mongo.db.users.delete_many({'colony': {'$nin': valid_colonies}, 'role': {'$ne': 'admin'}})
    print(f"Deleted {result.deleted_count} invalid users.")
    
    # Generate Dummy Users — 3 per colony, all approved
    print("Generating dummy users for demo...")
    dummy_users = [
        # Anna Nagar
        {"username": "arun_anna",    "first": "Arun",     "last": "Kumar",      "colony": "Anna Nagar",     "door": "A-101", "email": "arun@example.com",    "credits": 40},
        {"username": "priya_anna",   "first": "Priya",    "last": "Rajan",      "colony": "Anna Nagar",     "door": "A-102", "email": "priya@example.com",   "credits": 80},
        {"username": "meena_anna",   "first": "Meena",    "last": "Suresh",     "colony": "Anna Nagar",     "door": "A-103", "email": "meena@example.com",   "credits": 20},
        # Nungambakkam
        {"username": "ravi_nung",    "first": "Ravi",     "last": "Shankar",    "colony": "Nungambakkam",   "door": "N-201", "email": "ravi@example.com",    "credits": 10},
        {"username": "lakshmi_nung", "first": "Lakshmi",  "last": "Narayanan",  "colony": "Nungambakkam",   "door": "N-202", "email": "lakshmi@example.com", "credits": 60},
        {"username": "vinoth_nung",  "first": "Vinoth",   "last": "Raj",        "colony": "Nungambakkam",   "door": "N-203", "email": "vinoth@example.com",  "credits": 0},
        # T. Nagar
        {"username": "deepa_tng",    "first": "Deepa",    "last": "Krishnan",   "colony": "T. Nagar",       "door": "T-301", "email": "deepa@example.com",   "credits": 30},
        {"username": "suresh_tng",   "first": "Suresh",   "last": "Babu",       "colony": "T. Nagar",       "door": "T-302", "email": "suresh@example.com",  "credits": 50},
        {"username": "kavitha_tng",  "first": "Kavitha",  "last": "Murugan",    "colony": "T. Nagar",       "door": "T-303", "email": "kavitha@example.com", "credits": 15},
        # Alwarpet
        {"username": "balaji_alw",   "first": "Balaji",   "last": "Srinivasan", "colony": "Alwarpet",       "door": "AL-401","email": "balaji@example.com",  "credits": 70},
        {"username": "janani_alw",   "first": "Janani",   "last": "Vijay",      "colony": "Alwarpet",       "door": "AL-402","email": "janani@example.com",  "credits": 25},
        {"username": "praveen_alw",  "first": "Praveen",  "last": "Kumar",      "colony": "Alwarpet",       "door": "AL-403","email": "praveen@example.com", "credits": 5},
        # Gopalapuram
        {"username": "karthik_gop",  "first": "Karthik",  "last": "Raja",       "colony": "Gopalapuram",    "door": "G-501", "email": "karthik@example.com", "credits": 90},
        {"username": "anitha_gop",   "first": "Anitha",   "last": "Selvam",     "colony": "Gopalapuram",    "door": "G-502", "email": "anitha@example.com",  "credits": 35},
        {"username": "murugan_gop",  "first": "Murugan",  "last": "Pandian",    "colony": "Gopalapuram",    "door": "G-503", "email": "murugan@example.com", "credits": 0},
    ]
    
    for d in dummy_users:
        if not mongo.db.users.find_one({'username': d['username']}):
            u_data = {
                'username':      d['username'],
                'first_name':    d['first'],
                'last_name':     d['last'],
                'email':         d.get('email', ''),
                'phone':         "9876543210",
                'door_no':       d['door'],
                'colony':        d['colony'],
                'role':          'user',
                'status':        'approved',
                'password_hash': User.generate_hash("password123"),
                'credits':       d.get('credits', 0)
            }
            mongo.db.users.insert_one(u_data)
            print(f"  Added: {d['username']} ({d['colony']})")
        else:
            print(f"  Already exists: {d['username']}")

    print("\nDatabase population complete!")
    print("Dummy user credentials: username above / password: password123")
