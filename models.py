from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, landlord, tenant
    full_name = db.Column(db.String(200))
    id_number = db.Column(db.String(50))
    passport_number = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    landlord_properties = db.relationship('Property', backref='landlord', lazy=True)
    tenant_leases = db.relationship('Lease', backref='tenant', lazy=True, foreign_keys='Lease.tenant_id')
    maintenance_requests = db.relationship('MaintenanceRequest', backref='tenant', lazy=True)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    total_units = db.Column(db.Integer, nullable=False)
    occupied_units = db.Column(db.Integer, default=0)
    landlord_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    units = db.relationship('Unit', backref='property', lazy=True, cascade='all, delete-orphan')

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.String(50), nullable=False)
    rent_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='vacant')  # vacant, occupied
    bedrooms = db.Column(db.Integer, default=1)
    bathrooms = db.Column(db.Integer, default=1)
    square_feet = db.Column(db.Integer)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    
    # Relationships
    leases = db.relationship('Lease', backref='unit', lazy=True, cascade='all, delete-orphan')
    maintenance_requests = db.relationship('MaintenanceRequest', backref='unit', lazy=True)

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
    
    # Relationship
    payments = db.relationship('Payment', backref='lease', lazy=True, cascade='all, delete-orphan')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    transaction_code = db.Column(db.String(100), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # mpesa, bank
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    receipt_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='medium')  # low, medium, high, emergency
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships are defined in User and Unit models

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # payment_due, payment_approved, maintenance, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='notifications')