from pymongo import MongoClient

uri = 'mongodb+srv://aquaflow:Watersystem24.7@cluster0.foi8pyx.mongodb.net/smart_water_db?appName=Cluster0'
client = MongoClient(uri)
db = client.get_database()

# Delete the accidental new user created by Google Login
res1 = db.users.delete_one({'email': 'vsgpvsjd2006@gmail.com', 'username': {'$ne': 'Prakash'}})
print(f"Deleted {res1.deleted_count} duplicate users.")

# Print Prakash before
prakash = db.users.find_one({'username': 'Prakash'})
print("Prakash before:", prakash)

# Update Prakash
result = db.users.update_one(
    {'username': 'Prakash'},
    {'$set': {'email': 'vsgpvsjd2006@gmail.com'}}
)
print('Matched:', result.matched_count, 'Modified:', result.modified_count)

# Verify
print("Prakash after:", db.users.find_one({'username': 'Prakash'}))
