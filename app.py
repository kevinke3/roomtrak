from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Property, Unit, Lease, Payment, Message, Notification, MaintenanceRequest
from config import Config
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username='admin',
                email='admin@roomtrack.com',
                password='admin123',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin / admin123")

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'landlord':
            return redirect(url_for('landlord_dashboard'))
        elif current_user.role == 'tenant':
            return redirect(url_for('tenant_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    stats = {
        'total_users': User.query.count(),
        'total_properties': Property.query.count(),
        'total_landlords': User.query.filter_by(role='landlord').count(),
        'total_tenants': User.query.filter_by(role='tenant').count()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/create-user', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    user = User(
        username=data.get('username'),
        email=data.get('email'),
        password=data.get('password'),
        role=data.get('role')
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'User created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Admin Routes for Tenant Management
@app.route('/admin/register-tenant', methods=['GET', 'POST'])
@login_required
def admin_register_tenant():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Create tenant user
        tenant = User(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            role='tenant',
            full_name=data.get('full_name'),
            id_number=data.get('id_number'),
            passport_number=data.get('passport_number'),
            phone=data.get('phone')
        )
        
        try:
            db.session.add(tenant)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Tenant registered successfully', 'tenant_id': tenant.id})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # GET request - show form
    properties = Property.query.all()
    vacant_units = Unit.query.filter_by(status='vacant').all()
    return render_template('admin/register_tenant.html', properties=properties, vacant_units=vacant_units)

@app.route('/admin/assign-unit', methods=['POST'])
@login_required
def admin_assign_unit():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    tenant = User.query.get(data.get('tenant_id'))
    unit = Unit.query.get(data.get('unit_id'))
    
    if not tenant or not unit:
        return jsonify({'error': 'Tenant or unit not found'}), 404
    
    if unit.status != 'vacant':
        return jsonify({'error': 'Unit is not vacant'}), 400
    
    # Create lease
    lease = Lease(
        tenant_id=tenant.id,
        unit_id=unit.id,
        start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
        end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date(),
        monthly_rent=unit.rent_amount,
        security_deposit=data.get('security_deposit', 0),
        status='active'
    )
    
    # Update unit status
    unit.status = 'occupied'
    
    # Update property occupancy
    unit.property.occupied_units += 1
    
    try:
        db.session.add(lease)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Unit assigned successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/admin/tenants')
@login_required
def admin_tenants():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    tenants = User.query.filter_by(role='tenant').all()
    tenants_data = []
    
    for tenant in tenants:
        lease = Lease.query.filter_by(tenant_id=tenant.id, status='active').first()
        tenants_data.append({
            'tenant': tenant,
            'lease': lease,
            'unit': lease.unit if lease else None,
            'property': lease.unit.property if lease and lease.unit else None
        })
    
    return render_template('admin/tenants.html', tenants_data=tenants_data)

# Landlord Routes
@app.route('/landlord/dashboard')
@login_required
def landlord_dashboard():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    
    # Calculate stats
    total_units = sum([prop.total_units for prop in properties])
    occupied_units = sum([prop.occupied_units for prop in properties])
    total_rent = sum([unit.rent_amount for prop in properties for unit in prop.units if unit.status == 'occupied'])
    
    # Get recent payments
    recent_payments = []
    for prop in properties:
        for unit in prop.units:
            for lease in unit.leases:
                recent_payments.extend(lease.payments)
    
    # Sort by creation date and get latest 5
    recent_payments.sort(key=lambda x: x.created_at, reverse=True)
    recent_payments = recent_payments[:5]
    
    stats = {
        'total_properties': len(properties),
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': total_units - occupied_units,
        'total_rent': total_rent,
        'occupancy_rate': round((occupied_units / total_units * 100) if total_units > 0 else 0, 1)
    }
    
    return render_template('landlord/dashboard.html', stats=stats, properties=properties, payments=recent_payments)

@app.route('/landlord/properties')
@login_required
def landlord_properties():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    return render_template('landlord/properties.html', properties=properties)

@app.route('/landlord/payments')
@login_required
def landlord_payments():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    
    # Get all payments for this landlord's properties
    all_payments = []
    for prop in properties:
        for unit in prop.units:
            for lease in unit.leases:
                all_payments.extend(lease.payments)
    
    # Sort by creation date (newest first)
    all_payments.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('landlord/payments.html', payments=all_payments)

@app.route('/landlord/tenants')
@login_required
def landlord_tenants():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    
    # Get all tenants for this landlord's properties
    tenants = []
    for prop in properties:
        for unit in prop.units:
            for lease in unit.leases:
                if lease.status == 'active':
                    tenants.append({
                        'tenant': lease.tenant,
                        'lease': lease,
                        'unit': unit,
                        'property': prop
                    })
    
    return render_template('landlord/tenants.html', tenants=tenants)

# Landlord Routes for Enhanced Views
@app.route('/landlord/units')
@login_required
def landlord_units():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    units = Unit.query.filter(Unit.property_id.in_([p.id for p in properties])).all()
    
    return render_template('landlord/units.html', properties=properties, units=units)

@app.route('/landlord/maintenance-reports')
@login_required
def landlord_maintenance_reports():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    maintenance_requests = MaintenanceRequest.query.join(Unit).filter(Unit.property_id.in_(property_ids)).order_by(MaintenanceRequest.created_at.desc()).all()
    
    return render_template('landlord/maintenance_reports.html', maintenance_requests=maintenance_requests)

@app.route('/landlord/tenant-payments')
@login_required
def landlord_tenant_payments():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    
    # Get all payments for this landlord's properties
    all_payments = []
    for prop in properties:
        for unit in prop.units:
            for lease in unit.leases:
                payments = Payment.query.filter_by(lease_id=lease.id).all()
                for payment in payments:
                    all_payments.append({
                        'payment': payment,
                        'tenant': lease.tenant,
                        'unit': unit,
                        'property': prop
                    })
    
    # Sort by creation date (newest first)
    all_payments.sort(key=lambda x: x['payment'].created_at, reverse=True)
    
    return render_template('landlord/tenant_payments.html', payments_data=all_payments, today=datetime.now())

# Landlord Tenant Management Routes
@app.route('/landlord/add-tenant', methods=['GET', 'POST'])
@login_required
def landlord_add_tenant():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Create tenant user
        tenant = User(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            role='tenant',
            full_name=data.get('full_name'),
            id_number=data.get('id_number'),
            passport_number=data.get('passport_number'),
            phone=data.get('phone')
        )
        
        try:
            db.session.add(tenant)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Tenant registered successfully', 'tenant_id': tenant.id})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # GET request - show form
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    vacant_units = Unit.query.filter(Unit.property_id.in_([p.id for p in properties]), Unit.status == 'vacant').all()
    return render_template('landlord/add_tenant.html', properties=properties, vacant_units=vacant_units)

@app.route('/landlord/assign-unit', methods=['POST'])
@login_required
def landlord_assign_unit():
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    tenant = User.query.get(data.get('tenant_id'))
    unit = Unit.query.get(data.get('unit_id'))
    
    if not tenant or not unit:
        return jsonify({'error': 'Tenant or unit not found'}), 404
    
    # Verify the unit belongs to this landlord
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    if unit.property_id not in property_ids:
        return jsonify({'error': 'Unauthorized - Unit does not belong to you'}), 403
    
    if unit.status != 'vacant':
        return jsonify({'error': 'Unit is not vacant'}), 400
    
    # Create lease
    lease = Lease(
        tenant_id=tenant.id,
        unit_id=unit.id,
        start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
        end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date(),
        monthly_rent=unit.rent_amount,
        security_deposit=data.get('security_deposit', 0),
        status='active'
    )
    
    # Update unit status
    unit.status = 'occupied'
    
    # Update property occupancy
    unit.property.occupied_units += 1
    
    try:
        db.session.add(lease)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Unit assigned successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/landlord/remove-tenant/<int:tenant_id>', methods=['POST'])
@login_required
def landlord_remove_tenant(tenant_id):
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find the tenant's active lease
    lease = Lease.query.filter_by(tenant_id=tenant_id, status='active').first()
    
    if not lease:
        return jsonify({'error': 'No active lease found for this tenant'}), 404
    
    # Verify the lease belongs to this landlord's property
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    if lease.unit.property_id not in property_ids:
        return jsonify({'error': 'Unauthorized - Tenant does not belong to your property'}), 403
    
    # End the lease
    lease.status = 'ended'
    lease.end_date = datetime.now().date()
    
    # Free up the unit
    lease.unit.status = 'vacant'
    
    # Update property occupancy
    lease.unit.property.occupied_units -= 1
    
    # Create notification for tenant
    notification = Notification(
        user_id=tenant_id,
        title='Lease Ended',
        message=f'Your lease for unit {lease.unit.unit_number} has been ended by the landlord.',
        type='lease_ended'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Tenant removed successfully'})

@app.route('/landlord/delete-tenant/<int:tenant_id>', methods=['POST'])
@login_required
def landlord_delete_tenant(tenant_id):
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
    
    tenant = User.query.get(tenant_id)
    
    if not tenant or tenant.role != 'tenant':
        return jsonify({'error': 'Tenant not found'}), 404
    
    # Check if tenant has any active leases with this landlord
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    active_leases = Lease.query.filter_by(tenant_id=tenant_id, status='active').all()
    has_active_lease = any(lease.unit.property_id in property_ids for lease in active_leases)
    
    if has_active_lease:
        return jsonify({'error': 'Cannot delete tenant with active lease. Please remove them from the unit first.'}), 400
    
    # Delete tenant (only if they don't have active leases with this landlord)
    try:
        # Delete related records
        Payment.query.filter(Payment.lease.has(tenant_id=tenant_id)).delete(synchronize_session=False)
        MaintenanceRequest.query.filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        Lease.query.filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        Message.query.filter((Message.sender_id == tenant_id) | (Message.receiver_id == tenant_id)).delete(synchronize_session=False)
        Notification.query.filter_by(user_id=tenant_id).delete(synchronize_session=False)
        
        # Delete tenant user
        db.session.delete(tenant)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Tenant deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/payment/approve/<int:payment_id>', methods=['POST'])
@login_required
def approve_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # Verify the payment belongs to this landlord's property
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    if payment.lease.unit.property_id not in property_ids:
        return jsonify({'error': 'Unauthorized'}), 403
    
    payment.status = 'approved'
    payment.receipt_generated = True
    
    # Create notification for tenant
    notification = Notification(
        user_id=payment.lease.tenant_id,
        title='Payment Approved',
        message=f'Your payment of KES {payment.amount:,.2f} has been approved. Receipt has been generated.',
        type='payment_approved'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Payment approved successfully'})

@app.route('/api/payment/reject/<int:payment_id>', methods=['POST'])
@login_required
def reject_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # Verify the payment belongs to this landlord's property
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    if payment.lease.unit.property_id not in property_ids:
        return jsonify({'error': 'Unauthorized'}), 403
    
    payment.status = 'rejected'
    
    # Create notification for tenant
    notification = Notification(
        user_id=payment.lease.tenant_id,
        title='Payment Rejected',
        message=f'Your payment of KES {payment.amount:,.2f} was rejected. Please contact your landlord.',
        type='payment_rejected'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Payment rejected'})

@app.route('/api/landlord/create-property', methods=['POST'])
@login_required
def create_property():
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    property = Property(
        name=data.get('name'),
        address=data.get('address'),
        total_units=data.get('total_units'),
        occupied_units=0,
        landlord_id=current_user.id
    )
    
    try:
        db.session.add(property)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Property created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Tenant Routes
@app.route('/tenant/dashboard')
@login_required
def tenant_dashboard():
    if current_user.role != 'tenant':
        return redirect(url_for('index'))
    
    lease = Lease.query.filter_by(tenant_id=current_user.id, status='active').first()
    payments = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.created_at.desc()).all() if lease else []
    
    # Get notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all() if lease else []
    
    # Calculate next payment due date
    next_due_date = None
    if lease and payments:
        last_payment = payments[0]
        next_due_date = last_payment.due_date
    elif lease:
        next_due_date = datetime.now().date() + timedelta(days=30)
    
    return render_template('tenant/dashboard.html', 
                         lease=lease, 
                         payments=payments, 
                         notifications=notifications,
                         next_due_date=next_due_date,
                         timedelta=timedelta)

@app.route('/tenant/payments')
@login_required
def tenant_payments():
    if current_user.role != 'tenant':
        return redirect(url_for('index'))
    
    lease = Lease.query.filter_by(tenant_id=current_user.id, status='active').first()
    payments = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.created_at.desc()).all() if lease else []
    
    return render_template('tenant/payments.html', payments=payments)

@app.route('/tenant/submit-payment', methods=['POST'])
@login_required
def submit_payment():
    if current_user.role != 'tenant':
        return jsonify({'error': 'Unauthorized'}), 403
    
    lease = Lease.query.filter_by(tenant_id=current_user.id, status='active').first()
    if not lease:
        return jsonify({'error': 'No active lease found'}), 400
    
    data = request.get_json()
    
    # Check if there's already a pending payment for this month
    current_month = datetime.now().replace(day=1).date()
    existing_payment = Payment.query.filter(
        Payment.lease_id == lease.id,
        Payment.payment_date >= current_month,
        Payment.status == 'pending'
    ).first()
    
    if existing_payment:
        return jsonify({'error': 'You already have a pending payment for this month'}), 400
    
    payment = Payment(
        lease_id=lease.id,
        amount=lease.monthly_rent,
        payment_date=datetime.now().date(),
        due_date=datetime.now().date() + timedelta(days=30),
        transaction_code=data.get('transaction_code'),
        payment_method=data.get('payment_method'),
        status='pending'
    )
    
    db.session.add(payment)
    
    # Create notification for landlord
    notification = Notification(
        user_id=lease.unit.property.landlord_id,
        title='New Payment Submitted',
        message=f'Tenant {current_user.username} submitted a payment of KES {lease.monthly_rent:,.2f}. Transaction: {data.get("transaction_code")}',
        type='payment_submitted'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Payment submitted successfully'})

@app.route('/tenant/maintenance')
@login_required
def tenant_maintenance():
    if current_user.role != 'tenant':
        return redirect(url_for('index'))
    
    lease = Lease.query.filter_by(tenant_id=current_user.id, status='active').first()
    maintenance_requests = MaintenanceRequest.query.filter_by(tenant_id=current_user.id).order_by(MaintenanceRequest.created_at.desc()).all() if lease else []
    
    return render_template('tenant/maintenance.html', maintenance_requests=maintenance_requests)

@app.route('/tenant/submit-maintenance', methods=['POST'])
@login_required
def submit_maintenance():
    if current_user.role != 'tenant':
        return jsonify({'error': 'Unauthorized'}), 403
    
    lease = Lease.query.filter_by(tenant_id=current_user.id, status='active').first()
    if not lease:
        return jsonify({'error': 'No active lease found'}), 400
    
    data = request.get_json()
    
    # Create maintenance request
    maintenance = MaintenanceRequest(
        tenant_id=current_user.id,
        unit_id=lease.unit_id,
        title=data.get('title'),
        description=data.get('description'),
        urgency=data.get('urgency', 'medium')
    )
    
    db.session.add(maintenance)
    
    # Create notification for landlord
    notification = Notification(
        user_id=lease.unit.property.landlord_id,
        title='New Maintenance Request',
        message=f'Tenant {current_user.full_name or current_user.username} submitted a maintenance request: {data.get("title")}',
        type='maintenance_request'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Maintenance request submitted successfully'})

# API Routes for Charts and Data
@app.route('/api/landlord/payment-stats')
@login_required
def landlord_payment_stats():
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Sample data for charts - in production, you'd query actual payment data
    data = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'datasets': [{
            'label': 'Rent Collection (KES)',
            'data': [185000, 195000, 210000, 205000, 220000, 235000],
            'backgroundColor': '#3498db',
            'borderColor': '#2980b9',
            'borderWidth': 2
        }]
    }
    
    return jsonify(data)

@app.route('/api/landlord/occupancy-stats')
@login_required
def landlord_occupancy_stats():
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    
    total_units = sum([prop.total_units for prop in properties])
    occupied_units = sum([prop.occupied_units for prop in properties])
    vacant_units = total_units - occupied_units
    
    data = {
        'labels': ['Occupied', 'Vacant'],
        'datasets': [{
            'data': [occupied_units, vacant_units],
            'backgroundColor': ['#27ae60', '#e74c3c'],
            'borderWidth': 1
        }]
    }
    
    return jsonify(data)

@app.route('/api/tenant/payment-history')
@login_required
def tenant_payment_history():
    if current_user.role != 'tenant':
        return jsonify({'error': 'Unauthorized'}), 403
    
    lease = Lease.query.filter_by(tenant_id=current_user.id, status='active').first()
    if not lease:
        return jsonify({'error': 'No active lease'}), 400
    
    payments = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.payment_date).all()
    
    data = {
        'labels': [p.payment_date.strftime('%b %Y') for p in payments[-6:]],  # Last 6 months
        'datasets': [{
            'label': 'Payment History',
            'data': [p.amount for p in payments[-6:]],
            'backgroundColor': '#3498db',
            'borderColor': '#2980b9',
            'borderWidth': 2
        }]
    }
    
    return jsonify(data)

# Maintenance API Routes
@app.route('/api/maintenance/update-status/<int:request_id>', methods=['POST'])
@login_required
def update_maintenance_status(request_id):
    maintenance = MaintenanceRequest.query.get_or_404(request_id)
    
    # Verify the maintenance request belongs to this landlord's property
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    if maintenance.unit.property_id not in property_ids:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    maintenance.status = data.get('status')
    maintenance.updated_at = datetime.utcnow()
    
    # Create notification for tenant
    notification = Notification(
        user_id=maintenance.tenant_id,
        title='Maintenance Status Updated',
        message=f'Your maintenance request "{maintenance.title}" has been marked as {data.get("status").replace("_", " ")}.',
        type='maintenance_update'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Maintenance status updated'})

# API to get vacant units for a property
@app.route('/api/property/<int:property_id>/vacant-units')
@login_required
def get_vacant_units(property_id):
    vacant_units = Unit.query.filter_by(property_id=property_id, status='vacant').all()
    
    units_data = []
    for unit in vacant_units:
        units_data.append({
            'id': unit.id,
            'unit_number': unit.unit_number,
            'rent_amount': unit.rent_amount,
            'bedrooms': unit.bedrooms,
            'bathrooms': unit.bathrooms
        })
    
    return jsonify(units_data)

# API to create sample units for a property
@app.route('/api/property/<int:property_id>/create-sample-units', methods=['POST'])
@login_required
def create_sample_units(property_id):
    if current_user.role != 'admin' and current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
    
    property = Property.query.get_or_404(property_id)
    
    # Create sample units
    units_data = [
        {'unit_number': 'A101', 'rent_amount': 25000, 'bedrooms': 2, 'bathrooms': 1},
        {'unit_number': 'A102', 'rent_amount': 28000, 'bedrooms': 2, 'bathrooms': 2},
        {'unit_number': 'A201', 'rent_amount': 30000, 'bedrooms': 3, 'bathrooms': 2},
        {'unit_number': 'A202', 'rent_amount': 32000, 'bedrooms': 3, 'bathrooms': 2},
        {'unit_number': 'B101', 'rent_amount': 22000, 'bedrooms': 1, 'bathrooms': 1},
        {'unit_number': 'B102', 'rent_amount': 24000, 'bedrooms': 1, 'bathrooms': 1},
    ]
    
    for unit_data in units_data:
        unit = Unit(
            unit_number=unit_data['unit_number'],
            rent_amount=unit_data['rent_amount'],
            bedrooms=unit_data['bedrooms'],
            bathrooms=unit_data['bathrooms'],
            property_id=property_id
        )
        db.session.add(unit)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Sample units created successfully'})

# Notification Routes
@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': notification.is_read
        })
    
    return jsonify(notifications_data)

@app.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

# Message Routes
@app.route('/api/messages')
@login_required
def get_messages():
    # Get messages where current user is either sender or receiver
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
    received_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    messages = sent_messages + received_messages
    messages.sort(key=lambda x: x.created_at, reverse=True)
    
    messages_data = []
    for message in messages[:10]:  # Last 10 messages
        messages_data.append({
            'id': message.id,
            'subject': message.subject,
            'message': message.message,
            'sender': message.sender.username,
            'receiver': message.receiver.username,
            'is_read': message.is_read,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
            'direction': 'sent' if message.sender_id == current_user.id else 'received'
        })
    
    return jsonify(messages_data)

@app.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=data.get('receiver_id'),
        subject=data.get('subject'),
        message=data.get('message'),
        is_read=False
    )
    
    db.session.add(message)
    
    # Create notification for receiver
    notification = Notification(
        user_id=data.get('receiver_id'),
        title='New Message',
        message=f'You have a new message from {current_user.username}',
        type='new_message'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Message sent successfully'})

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    init_db()
    print("RoomTrack is running on http://localhost:5000")
    print("\nDemo Accounts:")
    print("Admin:    admin / admin123")
    print("Landlord: landlord1 / pass123")
    print("Tenant:   tenant1 / pass123")
    app.run(debug=True, host='0.0.0.0', port=5000)