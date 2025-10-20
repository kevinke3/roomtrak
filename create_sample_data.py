from app import app, db
from models import User, Property, Unit, Lease, Payment
from datetime import datetime, timedelta

def create_sample_data():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if sample data already exists
        if User.query.filter_by(username='landlord1').first():
            print("Sample data already exists!")
            return
        
        print("Creating sample data...")
        
        # Create landlord
        landlord = User(
            username='landlord1',
            email='landlord@roomtrack.com',
            password='pass123',
            role='landlord'
        )
        db.session.add(landlord)
        
        # Create tenant
        tenant = User(
            username='tenant1',
            email='tenant@roomtrack.com',
            password='pass123',
            role='tenant'
        )
        db.session.add(tenant)
        
        db.session.commit()
        print("Created users...")
        
        # Create property
        property = Property(
            name='Sunrise Apartments',
            address='123 Main Street, Nairobi, Kenya',
            total_units=12,
            occupied_units=5,
            landlord_id=landlord.id
        )
        db.session.add(property)
        db.session.commit()
        print("Created property...")
        
        # Create unit
        unit = Unit(
            unit_number='A101',
            rent_amount=25000.00,
            status='occupied',
            property_id=property.id
        )
        db.session.add(unit)
        db.session.commit()
        print("Created unit...")
        
        # Create lease
        lease = Lease(
            tenant_id=tenant.id,
            unit_id=unit.id,
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=365),
            monthly_rent=25000.00,
            security_deposit=25000.00,
            status='active'
        )
        db.session.add(lease)
        db.session.commit()
        print("Created lease...")
        
        # Create sample payments
        payments_data = [
            {
                'transaction_code': 'MPESA123456',
                'payment_method': 'mpesa',
                'status': 'approved',
                'days_ago': 30
            },
            {
                'transaction_code': 'MPESA789012',
                'payment_method': 'mpesa', 
                'status': 'approved',
                'days_ago': 60
            },
            {
                'transaction_code': 'MPESA345678',
                'payment_method': 'mpesa',
                'status': 'pending',
                'days_ago': 0
            }
        ]
        
        for i, payment_data in enumerate(payments_data):
            payment = Payment(
                lease_id=lease.id,
                amount=25000.00,
                payment_date=datetime.now().date() - timedelta(days=payment_data['days_ago']),
                due_date=datetime.now().date() + timedelta(days=30),
                transaction_code=payment_data['transaction_code'],
                payment_method=payment_data['payment_method'],
                status=payment_data['status'],
                receipt_generated=(payment_data['status'] == 'approved')
            )
            db.session.add(payment)
        
        db.session.commit()
        print("Created payments...")
        
        print("Sample data created successfully!")
        print("\nDemo Accounts:")
        print("Admin:     admin / admin123")
        print("Landlord:  landlord1 / pass123") 
        print("Tenant:    tenant1 / pass123")

if __name__ == '__main__':
    create_sample_data()
