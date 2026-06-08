from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True, cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    orders_as_buyer = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy='dynamic')
    orders_as_seller = db.relationship('Order', foreign_keys='Order.seller_id', backref='seller_orders', lazy='dynamic')

    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    image_filename = db.Column(db.String(200))
    image_hash = db.Column(db.String(64))  # For duplicate detection
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    messages = db.relationship('Message', backref='product', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='product', lazy=True, cascade='all, delete-orphan')
    fraud_alerts = db.relationship('FraudAlert', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.title}>'

class FraudAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # e.g., 'Duplicate Image'
    details = db.Column(db.Text)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FraudAlert {self.id} - {self.alert_type}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    sender_email = db.Column(db.String(120), nullable=False)
    sender_phone = db.Column(db.String(20))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Message {self.id}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    buyer_name = db.Column(db.String(100), nullable=False)
    buyer_email = db.Column(db.String(120), nullable=False)
    buyer_phone = db.Column(db.String(20), nullable=False)
    buyer_address = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    payment_method = db.Column(db.String(50), default='cash')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    @staticmethod
    def generate_order_number():
        """Generate a unique order number"""
        import random
        import string
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits, k=4))
        return f'ORD-{timestamp}-{random_part}'

# Categories for products
CATEGORIES = [
    'Mobiles', 'Electronics', 'Cars', 'Bikes', 'Houses & Apartments',
    'Furniture', 'Fashion', 'Books', 'Sports', 'Kids', 'Services', 'Other'
]

# Conditions for products
CONDITIONS = ['New', 'Like New', 'Good', 'Fair', 'Poor']
