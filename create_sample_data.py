from app import app, db
from models import User, Property, Unit, Lease, Payment, MaintenanceRequest
from datetime import datetime, timedelta

def create_sample_data():
    with app.app_context():
        # Check if sample data already exists
        if User.query.filter_by(username='tenant1').first():
            print("Sample data already exists!")
            return
        
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
            passport_number='A1234567',
            phone='+254798765432'
        )
        db.session.add(tenant)
        db.session.commit()
        print("Created tenant...")
        
        # Create property
        property = Property(
            name='Sunrise Apartments',
            address='123 Main Street, Nairobi, Kenya',
            total_units=12,
            occupied_units=3,
            landlord_id=landlord.id
        )
        db.session.add(property)
        db.session.commit()
        print("Created property...")
        
        # Create sample units
        units_data = [
            {'unit_number': 'A101', 'rent_amount': 25000, 'bedrooms': 2, 'bathrooms': 1, 'status': 'occupied'},
            {'unit_number': 'A102', 'rent_amount': 28000, 'bedrooms': 2, 'bathrooms': 2, 'status': 'occupied'},
            {'unit_number': 'A201', 'rent_amount': 30000, 'bedrooms': 3, 'bathrooms': 2, 'status': 'occupied'},
            {'unit_number': 'A202', 'rent_amount': 32000, 'bedrooms': 3, 'bathrooms': 2, 'status': 'vacant'},
            {'unit_number': 'B101', 'rent_amount': 22000, 'bedrooms': 1, 'bathrooms': 1, 'status': 'vacant'},
            {'unit_number': 'B102', 'rent_amount': 24000, 'bedrooms': 1, 'bathrooms': 1, 'status': 'vacant'},
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
        print("Created units...")
        
        # Create lease for tenant1
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
        print("Created lease...")
        
        # Create sample payments
        payments_data = [
            {
                'transaction_code': 'MPESA123456',
                'payment_method': 'mpesa',
                'status': 'approved',
                'days_ago': 60
            },
            {
                'transaction_code': 'MPESA789012',
                'payment_method': 'mpesa', 
                'status': 'approved',
                'days_ago': 30
            },
            {
                'transaction_code': 'MPESA345678',
                'payment_method': 'mpesa',
                'status': 'pending',
                'days_ago': 0
            }
        ]
        
        for payment_data in payments_data:
            payment = Payment(
                lease_id=lease.id,
                amount=unit_a101.rent_amount,
                payment_date=datetime.now().date() - timedelta(days=payment_data['days_ago']),
                due_date=datetime.now().date() + timedelta(days=30),
                transaction_code=payment_data['transaction_code'],
                payment_method=payment_data['payment_method'],
                status=payment_data['status'],
                receipt_generated=(payment_data['status'] == 'approved')
            )
            db.session.add(payment)
        
        # Create sample maintenance requests
        maintenance_data = [
            {
                'title': 'Leaking Kitchen Faucet',
                'description': 'The kitchen faucet has been leaking constantly for the past 2 days. It\'s wasting water and creating a puddle under the sink.',
                'urgency': 'medium',
                'days_ago': 5
            },
            {
                'title': 'AC Not Working',
                'description': 'The air conditioning unit in the living room stopped working. It makes strange noises but doesn\'t cool the room.',
                'urgency': 'high',
                'days_ago': 2
            },
            {
                'title': 'Broken Window Handle',
                'description': 'The handle on the bedroom window is broken, making it difficult to open and close the window properly.',
                'urgency': 'low',
                'days_ago': 10
            }
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
        print("Created payments and maintenance requests...")
        
        print("✅ Sample data created successfully!")
        print("\n📋 Demo Accounts:")
        print("   Admin:    admin / admin123")
        print("   Landlord: landlord1 / pass123") 
        print("   Tenant:   tenant1 / pass123")
        print("\n🏢 Sample Property: Sunrise Apartments with 6 units")
        print("   - 3 occupied units, 3 vacant units")
        print("   - Tenant1 is assigned to Unit A101")

if __name__ == '__main__':
    create_sample_data()