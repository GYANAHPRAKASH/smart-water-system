from app import create_app, mongo
from app.models import User

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create Initial Admin if not exists
        if not mongo.db.users.find_one({'username': 'Prakash'}):
            admin_data = {
                'username': 'Prakash',
                'role': 'admin',
                'status': 'approved',
                'first_name': 'Admin',
                'last_name': 'User',
                'phone': '9999999999',
                'door_no': '001',
                'colony': 'Admin Office',
                'password_hash': User.generate_hash('admin123'),
                'credits': 0
            }
            mongo.db.users.insert_one(admin_data)
            print("Admin user created.")
    app.run(debug=True)
