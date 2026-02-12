from app import create_app, db
from app.models import User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

if __name__ == '__main__':
    with app.app_context():
        # Import models to ensure they are registered
        from app.models import User, Complaint, Schedule, WaterUsage
        db.create_all()
        # Create Initial Admin if not exists
        if not User.query.filter_by(username='Prakash').first():
            admin = User(username='Prakash', role='admin', status='approved',
                         first_name='Admin', last_name='User', phone='9999999999',
                         door_no='001', colony='Admin Office')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created.")
    app.run(debug=True)
