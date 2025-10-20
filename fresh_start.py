import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Create a temporary app to initialize the database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///roomtrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'roomtrack-secret-key-2024'

db = SQLAlchemy(app)

# Define the models exactly as in models.py
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(200))
    id_number = db.Column(db.String(50))
    passport_number = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    total_units = db.Column(db.Integer, nullable=False)
    occupied_units = db.Column(db.Integer, default=0)
    landlord_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.String(50), nullable=False)
    rent_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='vacant')
    bedrooms = db.Column(db.Integer, default=1)
    bathrooms = db.Column(db.Integer, default=1)
    square_feet = db.Column(db.Integer)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)

class Lease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    monthly_rent = db.Column(db.Float, nullable=False)
    security_deposit = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    transaction_code = db.Column(db.String(100), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')
    receipt_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def setup_database():
    with app.app_context():
        # Drop all tables if they exist
        db.drop_all()
        print("🗑️  Dropped all existing tables")
        
        # Create all tables with new schema
        db.create_all()
        print("✅ Created all tables with new schema")
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@roomtrack.com',
            password='admin123',
            role='admin'
        )
        db.session.add(admin)
        
        # Create landlord user
        landlord = User(
            username='landlord1',
            email='landlord@roomtrack.com',
            password='pass123',
            role='landlord',
            full_name='John Landlord',
            phone='+254712345678'
        )
        db.session.add(landlord)
        
        db.session.commit()
        print("✅ Created admin user: admin / admin123")
        print("✅ Created landlord user: landlord1 / pass123")
        
        # Verify the schema
        print("\n📊 Database Schema Verified:")
        print(f"   - User table has full_name: {'full_name' in [col.name for col in User.__table__.columns]}")
        print(f"   - User table has id_number: {'id_number' in [col.name for col in User.__table__.columns]}")
        print(f"   - MaintenanceRequest table exists: {MaintenanceRequest.__table__ is not None}")

if __name__ == '__main__':
    setup_database()
    print("\n🎉 Database setup completed successfully!")
