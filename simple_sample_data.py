import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///roomtrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'roomtrack-secret-key-2024'

db = SQLAlchemy(app)

# Import models (we'll define them inline to avoid import issues)
class User(db.Model):
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

def create_sample_data():
    with app.app_context():
        print("Creating sample data...")
        
        # Get landlord
        landlord = User.query.filter_by(username='landlord1').first()
        
        # Create tenant
        tenant = User(
            username='tenant1',
            email='tenant@roomtrack.com',
            password='pass123',
            role='tenant',
            full_name='Jane Tenant',
            id_number='12345678',
            phone='+254798765432'
        )
        db.session.add(tenant)
        db.session.commit()
        print("✅ Created tenant user")
        
        # Create property
        property = Property(
            name='Sunrise Apartments',
            address='123 Main Street, Nairobi, Kenya',
            total_units=6,
            occupied_units=1,
            landlord_id=landlord.id
        )
        db.session.add(property)
        db.session.commit()
        print("✅ Created property")
        
        # Create units
        units_data = [
            {'unit_number': 'A101', 'rent_amount': 25000, 'bedrooms': 2, 'bathrooms': 1, 'status': 'occupied'},
            {'unit_number': 'A102', 'rent_amount': 28000, 'bedrooms': 2, 'bathrooms': 2, 'status': 'vacant'},
            {'unit_number': 'A201', 'rent_amount': 30000, 'bedrooms': 3, 'bathrooms': 2, 'status': 'vacant'},
        ]
        
        for unit_data in units_data:
            unit = Unit(
                unit_number=unit_data['unit_number'],
                rent_amount=unit_data['rent_amount'],
                bedrooms=unit_data['bedrooms'],
                bathrooms=unit_data['bathrooms'],
                status=unit_data['status'],
                property_id=property.id
            )
            db.session.add(unit)
        
        db.session.commit()
        print("✅ Created units")
        
        # Create lease
        unit_a101 = Unit.query.filter_by(unit_number='A101').first()
        lease = Lease(
            tenant_id=tenant.id,
            unit_id=unit_a101.id,
            start_date=datetime.now().date() - timedelta(days=90),
            end_date=datetime.now().date() + timedelta(days=275),
            monthly_rent=unit_a101.rent_amount,
            security_deposit=unit_a101.rent_amount,
            status='active'
        )
        db.session.add(lease)
        db.session.commit()
        print("✅ Created lease")
        
        # Create payments
        payments_data = [
            {'transaction_code': 'MPESA123456', 'status': 'approved', 'days_ago': 60},
            {'transaction_code': 'MPESA789012', 'status': 'approved', 'days_ago': 30},
            {'transaction_code': 'MPESA345678', 'status': 'pending', 'days_ago': 0},
        ]
        
        for payment_data in payments_data:
            payment = Payment(
                lease_id=lease.id,
                amount=unit_a101.rent_amount,
                payment_date=datetime.now().date() - timedelta(days=payment_data['days_ago']),
                due_date=datetime.now().date() + timedelta(days=30),
                transaction_code=payment_data['transaction_code'],
                payment_method='mpesa',
                status=payment_data['status'],
                receipt_generated=(payment_data['status'] == 'approved')
            )
            db.session.add(payment)
        
        print("✅ Created payments")
        
        # Create maintenance requests
        maintenance_data = [
            {
                'title': 'Leaking Kitchen Faucet',
                'description': 'The kitchen faucet has been leaking constantly.',
                'urgency': 'medium',
                'days_ago': 5
            },
        ]
        
        for maintenance_item in maintenance_data:
            maintenance = MaintenanceRequest(
                tenant_id=tenant.id,
                unit_id=unit_a101.id,
                title=maintenance_item['title'],
                description=maintenance_item['description'],
                urgency=maintenance_item['urgency'],
                status='pending',
                created_at=datetime.now() - timedelta(days=maintenance_item['days_ago'])
            )
            db.session.add(maintenance)
        
        db.session.commit()
        print("✅ Created maintenance requests")
        
        print("\n🎉 SAMPLE DATA CREATED SUCCESSFULLY!")
        print("\n📋 DEMO ACCOUNTS:")
        print("   👑 Admin:    admin / admin123")
        print("   🏠 Landlord: landlord1 / pass123") 
        print("   👤 Tenant:   tenant1 / pass123")

if __name__ == '__main__':
    create_sample_data()
