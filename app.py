from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Property, Unit, Lease, Payment, Message, Notification
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

# Sample data initialization
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username='admin',
                email='admin@roomtrack.com',
                password='admin123',  # In production, hash this
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()

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
        password = request.form.get('password')  # In production, use proper authentication
        
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

# Landlord Routes
@app.route('/landlord/dashboard')
@login_required
def landlord_dashboard():
    if current_user.role != 'landlord':
        return redirect(url_for('index'))
    
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    total_rent = sum([unit.rent_amount for prop in properties for unit in prop.units if unit.status == 'occupied'])
    
    # Payment statistics for charts
    payments = Payment.query.join(Lease).join(Unit).filter(Unit.property_id.in_([p.id for p in properties])).all()
    
    stats = {
        'total_properties': len(properties),
        'total_units': sum([prop.total_units for prop in properties]),
        'occupied_units': sum([prop.occupied_units for prop in properties]),
        'total_rent': total_rent
    }
    
    return render_template('landlord/dashboard.html', stats=stats, properties=properties)

@app.route('/landlord/payments')
@login_required
def landlord_payments():
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    payments = Payment.query.join(Lease).join(Unit).filter(Unit.property_id.in_(property_ids)).all()
    return render_template('landlord/payments.html', payments=payments)

@app.route('/api/payment/approve/<int:payment_id>', methods=['POST'])
@login_required
def approve_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'approved'
    payment.receipt_generated = True
    
    # Create notification for tenant
    notification = Notification(
        user_id=payment.lease.tenant_id,
        title='Payment Approved',
        message=f'Your payment of KES {payment.amount} has been approved.',
        type='payment_approved'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

# Tenant Routes
@app.route('/tenant/dashboard')
@login_required
def tenant_dashboard():
    if current_user.role != 'tenant':
        return redirect(url_for('index'))
    
    lease = Lease.query.filter_by(tenant_id=current_user.id, status='active').first()
    payments = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.created_at.desc()).all() if lease else []
    
    return render_template('tenant/dashboard.html', lease=lease, payments=payments)

@app.route('/tenant/submit-payment', methods=['POST'])
@login_required
def submit_payment():
    if current_user.role != 'tenant':
        return jsonify({'error': 'Unauthorized'}), 403
    
    lease = Lease.query.filter_by(tenant_id=current_user.id, status='active').first()
    if not lease:
        return jsonify({'error': 'No active lease found'}), 400
    
    data = request.get_json()
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
        message=f'Tenant {current_user.username} submitted a payment of KES {lease.monthly_rent}',
        type='payment_submitted'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True})

# API Routes for Charts
@app.route('/api/landlord/payment-stats')
@login_required
def landlord_payment_stats():
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    payments = Payment.query.join(Lease).join(Unit).filter(Unit.property_id.in_(property_ids)).all()
    
    # Sample data for charts
    data = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'datasets': [{
            'label': 'Rent Collection',
            'data': [65000, 59000, 80000, 81000, 56000, 75000],
            'backgroundColor': '#3498db'
        }]
    }
    
    return jsonify(data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)