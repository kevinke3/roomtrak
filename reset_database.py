import os
from app import app, db
from models import User

def reset_database():
    with app.app_context():
        # Delete database file if it exists
        if os.path.exists('roomtrack.db'):
            os.remove('roomtrack.db')
            print("Removed existing database")
        
        # Create all tables with new schema
        db.create_all()
        print("Created new database tables")
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@roomtrack.com',
            password='admin123',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Created admin user: admin / admin123")

if __name__ == '__main__':
    reset_database()
