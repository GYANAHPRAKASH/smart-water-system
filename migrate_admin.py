from pymongo import MongoClient
import sys

uri = 'mongodb+srv://aquaflow:Watersystem24.7@cluster0.foi8pyx.mongodb.net/?appName=Cluster0'
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping') # Test connection
except Exception as e:
    print("Could not connect to MongoDB:", e)
    sys.exit(1)

test_db = client['test']
prakash = test_db.users.find_one({'username': 'Prakash'})

print('Found Prakash in test db:', prakash is not None)

if prakash:
    print('Migrating admin account from test to smart_water_db...')
    smart_db = client['smart_water_db']
    
    # Check if we already migrated
    if not smart_db.users.find_one({'username': 'Prakash'}):
        # Insert Prakash and other users if needed, but let's just do Prakash for now to be safe
        smart_db.users.insert_one(prakash)
        print('Prakash copied to smart_water_db.')
    else:
        print('Prakash already exists in smart_water_db.')
        
    print('Updating Prakash email to vsgpvsjd2006@gmail.com...')
    smart_db.users.update_one({'username': 'Prakash'}, {'$set': {'email': 'vsgpvsjd2006@gmail.com'}})
    
    # Delete the accidental duplicate user the user just created via Google Login
    res = smart_db.users.delete_one({'username': 'vsgpvsjd2006'})
    if res.deleted_count > 0:
        print('Deleted accidental duplicate account "vsgpvsjd2006".')
        
    print('\nSUCCESS! You can now log into your Admin account using "Continue with Google"!')
else:
    print('Prakash not found in the "test" database.')
