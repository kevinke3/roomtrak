from app import app, db
from models import User, Property, Unit, Lease, Payment
from datetime import datetime, timedelta

def create_sample_data():
    with app.app_context():
        # Clear existing data (optional - be careful in production)
        # db.drop_all()
        # db.create_all()
        
        # Get users
        landlord = User.query.filter_by(username='landlord1').first()
        tenant = User.query.filter_by(username='tenant1').first()
        
        # Create a property if it doesn't exist
        if not Property.query.first():
            property = Property(
                name='Sunrise Apartments',
                address='123 Main Street, Nairobi',
                total_units=10,
                occupied_units=3,
                landlord_id=landlord.id
            )
            db.session.add(property)
            db.session.commit()
            
            # Create units
            unit1 = Unit(
                unit_number='A101',
                rent_amount=25000.00,
                status='occupied',
                property_id=property.id
            )
            db.session.add(unit1)
            db.session.commit()
            
            # Create lease
            lease = Lease(
                tenant_id=tenant.id,
                unit_id=unit1.id,
                start_date=datetime.now().date(),
                end_date=datetime.now().date() + timedelta(days=365),
                monthly_rent=25000.00,
                security_deposit=25000.00,
                status='active'
            )
            db.session.add(lease)
            db.session.commit()
            
            # Create sample payment
            payment = Payment(
                lease_id=lease.id,
                amount=25000.00,
                payment_date=datetime.now().date(),
                due_date=datetime.now().date() + timedelta(days=30),
                transaction_code='MPESA123456',
                payment_method='mpesa',
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            print("Sample data created successfully!")
        else:
            print("Sample data already exists!")

if __name__ == '__main__':
    create_sample_data()
