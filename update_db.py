from app import create_app, db
from app.models import Schedule

app = create_app()

with app.app_context():
    # Drop the Schedule table and recreate it
    print("Dropping Schedule table...")
    Schedule.__table__.drop(db.engine)
    print("Recreating Schedule table...")
    db.create_all()
    print("Database updated successfully!")
