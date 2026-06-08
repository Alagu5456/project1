import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, and_
from app import app, db
from models import User, Product, Message, Order, FraudAlert, CATEGORIES
from forms import LoginForm, RegisterForm, ProductForm, MessageForm, SearchForm, OrderForm
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

# Load Price Prediction Model and Encoders
try:
    with open('price_prediction_model.pkl', 'rb') as f:
        price_model = pickle.load(f)
    with open('brand_encoder.pkl', 'rb') as f:
        brand_encoder = pickle.load(f)
    with open('condition_encoder.pkl', 'rb') as f:
        condition_encoder = pickle.load(f)
    with open('category_encoder.pkl', 'rb') as f:
        category_encoder = pickle.load(f)
    print("Price prediction model loaded successfully.")
except Exception as e:
    print(f"Error loading price prediction model: {e}")
    price_model = None

# Heuristic Condition Detection using Image Properties
# This provides a deterministic and logical guess based on image quality
# until a real CNN model is trained with user data.
def detect_condition_from_image(image_path):
    try:
        from PIL import Image, ImageStat, ImageFilter
        import math

        img = Image.open(image_path).convert('L') # Convert to grayscale
        
        # 1. Calculate Sharpness/Brightness
        stat = ImageStat.Stat(img)
        brightness = stat.mean[0]
        std_dev = stat.stddev[0]
        
        # 2. Advanced: Edge Detection for Cracks/Damage
        # Damaged items (broken screens, scratches) often have very high high-frequency noise (edges)
        edges = img.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        edge_density = edge_stat.mean[0] # Average intensity of edges
        
        # Heuristic Logic:
        # Very high edge density often means Chaos/Cracks -> Poor
        # Very low brightness -> Poor (Bad photo usually correlates with bad care)
        # High Brightness + Good Contrast + Low-Medium Edge Density -> New/Like New
        
        score = (std_dev * 2) + (brightness / 2)
        
        if edge_density > 100: # Tune this threshold. High edge density = "Too Busy" / Cracks
             return 'Poor'
        elif score > 150 and edge_density < 50:
            return 'New'
        elif score > 120:
            return 'Like New'
        elif score > 80:
            return 'Good'
        elif score > 50:
            return 'Fair'
        else:
            return 'Poor'
            
    except Exception as e:
        print(f"Error in heuristic detection: {e}")
        # Fallback
        return 'Good'

@app.route('/detect_condition', methods=['POST'])
def detect_condition():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
        
    if file:
        try:
            # Save temporarily to process
            temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            filename = secure_filename(file.filename)
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            
            # Detect condition
            detected_condition = detect_condition_from_image(filepath)
            
            # Clean up
            try:
                os.remove(filepath)
            except:
                pass
                
            return jsonify({'condition': detected_condition})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

def calculate_image_hash(image_path):
    """Calculate perceptual hash of an image for duplicate detection"""
    try:
        from PIL import Image
        # Open, resize to 8x8 and convert to grayscale
        img = Image.open(image_path).resize((8, 8), Image.Resampling.LANCZOS).convert('L')
        # Calculate average pixel value
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        # Create 64-bit hash
        bits = ''.join(['1' if x > avg else '0' for x in pixels])
        # Convert binary string to hex for storage
        return hex(int(bits, 2))[2:]
    except Exception as e:
        print(f"Error hashing image: {e}")
        return None

@app.route('/predict_price', methods=['POST'])
def predict_price():
    if not price_model:
        return jsonify({'error': 'Prediction model not available'}), 500
    
    data = request.get_json()
    
    try:
        brand = data.get('brand')
        category = data.get('category')
        year = float(data.get('year'))
        condition = data.get('condition')
        original_price = float(data.get('original_price'))
        usage_str = data.get('usage')
        
        # Calculate Age
        current_year = datetime.now().year
        age = current_year - year
        if age < 0: age = 0
        
        # Estimate Usage Hours (Approximate based on selection)
        # Assuming average 4 hours/day usage
        hours_per_month = 4 * 30
        usage_hours = 0
        
        if usage_str == 'Less than 1 month':
            usage_hours = 15 * 4 # ~2 weeks
        elif usage_str == '1-6 months':
            usage_hours = 3 * hours_per_month
        elif usage_str == '6-12 months':
            usage_hours = 9 * hours_per_month
        elif usage_str == '1-2 years':
            usage_hours = 18 * hours_per_month
        elif usage_str == 'More than 2 years':
            usage_hours = 36 * hours_per_month # 3 years
        else:
            usage_hours = 12 * hours_per_month # Default backup
            
        # Encode Categorical Variables
        # Handle unseen labels safely
        try:
            brand_encoded = brand_encoder.transform([brand])[0]
        except ValueError:
            # Fallback: Find most common brand or just use a random one from encoder to avoid crash
            # Better approach: map to a "Other" or "Generic" if it exists, else 0
            # Assuming 'Generic' exists in our synthetic data for 'Other' category
            try:
                brand_encoded = brand_encoder.transform(['Generic'])[0]
            except:
                brand_encoded = 0
            
        try:
            condition_encoded = condition_encoder.transform([condition])[0]
        except ValueError:
            condition_encoded = 0
            
        try:
            category_encoded = category_encoder.transform([category])[0]
        except ValueError:
            category_encoded = 0 # Default if unknown
            
        # Create Feature Vector
        # Features: ['brand', 'category', 'age', 'condition', 'usage_hours', 'original_price']
        features = np.array([[brand_encoded, category_encoded, age, condition_encoded, usage_hours, original_price]])
        
        # Predict
        predicted_price = price_model.predict(features)[0]
        
        return jsonify({'predicted_price': round(predicted_price, 2)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/')
def index():
    search_form = SearchForm()
    
    # Get query parameters
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Build search query
    products_query = Product.query.filter(Product.is_available == True)
    
    if query:
        products_query = products_query.filter(
            or_(
                Product.title.contains(query),
                Product.description.contains(query)
            )
        )
    
    if category:
        products_query = products_query.filter(Product.category == category)
    
    if location:
        products_query = products_query.filter(Product.location.contains(location))
    
    if min_price is not None:
        products_query = products_query.filter(Product.price >= min_price)
    
    if max_price is not None:
        products_query = products_query.filter(Product.price <= max_price)
    
    # Get products ordered by creation date
    products = products_query.order_by(Product.created_at.desc()).limit(20).all()
    
    # Get featured products (latest 6)
    featured_products = Product.query.filter(Product.is_available == True).order_by(Product.created_at.desc()).limit(6).all()
    
    return render_template('index.html', 
                         products=products, 
                         featured_products=featured_products,
                         categories=CATEGORIES,
                         search_form=search_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('register.html', form=form)
        
        # Create new user
        user = User(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            location=form.location.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Basic protection: Check if user is admin
    if not current_user.is_admin:
        flash('Access denied. Admin area only.', 'error')
        return redirect(url_for('index'))

    # Stats
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    
    # Revenue (Total from completed orders)
    completed_orders = Order.query.filter_by(status='completed').all()
    total_revenue = sum(order.total_amount for order in completed_orders)
    
    # Commission (10%)
    commission = total_revenue * 0.10
    
    # Fraud Alerts
    fraud_alerts = FraudAlert.query.filter_by(is_resolved=False).order_by(FraudAlert.created_at.desc()).all()
    fraud_alerts_count = len(fraud_alerts)
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         commission=commission,
                         fraud_alerts=fraud_alerts,
                         fraud_alerts_count=fraud_alerts_count)

@app.route('/dashboard')
@login_required
def dashboard():
    user_products = Product.query.filter_by(user_id=current_user.id).order_by(Product.created_at.desc()).all()
    
    # Get unread messages count
    unread_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    
    return render_template('dashboard.html', 
                         products=user_products,
                         unread_count=unread_count)

@app.route('/post_ad', methods=['GET', 'POST'])
@login_required
def post_ad():
    form = ProductForm()
    if form.validate_on_submit():
        # Handle file upload
        image_filename = None
        if form.image.data:
            image_filename = secure_filename(form.image.data.filename)
            # Add timestamp to avoid conflicts
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            image_filename = timestamp + image_filename
            
            # Create upload directory if it doesn't exist
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_path, exist_ok=True)
            
            # Save the file
            full_path = os.path.join(upload_path, image_filename)
            form.image.data.save(full_path)
            
            # Calculate image hash
            image_hash = calculate_image_hash(full_path)
            
            # Check for duplicates
            is_fraud = False
            if image_hash:
                duplicate = Product.query.filter_by(image_hash=image_hash).first()
                if duplicate:
                    is_fraud = True
                    flash('Warning: This image has been detected in another listing. This has been flagged for admin review.', 'warning')

        
        # Create product
        product = Product(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            condition=form.condition.data,
            location=form.location.data,
            image_filename=image_filename,
            image_hash=image_hash if image_filename else None,
            user_id=current_user.id
        )
        
        db.session.add(product)
        db.session.flush() # Flush to get ID
        
        # Create fraud alert if needed
        if is_fraud:
            alert = FraudAlert(
                product_id=product.id,
                alert_type='Duplicate Image',
                details=f'Image matches existing product ID {duplicate.id}',
                is_resolved=False
            )
            db.session.add(alert)
        
        db.session.commit()
        
        flash('Your ad has been posted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('post_ad.html', form=form)

@app.route('/edit_ad/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_ad(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if user owns this product
    if product.user_id != current_user.id:
        flash('You can only edit your own ads', 'error')
        return redirect(url_for('dashboard'))
    
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        # Handle file upload
        if form.image.data:
            image_filename = secure_filename(form.image.data.filename)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            image_filename = timestamp + image_filename
            
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_path, exist_ok=True)
            
            form.image.data.save(os.path.join(upload_path, image_filename))
            product.image_filename = image_filename
        
        # Update product
        product.title = form.title.data
        product.description = form.description.data
        product.price = form.price.data
        product.category = form.category.data
        product.condition = form.condition.data
        product.location = form.location.data
        
        db.session.commit()
        flash('Ad updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_ad.html', form=form, product=product)

@app.route('/delete_ad/<int:product_id>')
@login_required
def delete_ad(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if user owns this product
    if product.user_id != current_user.id:
        flash('You can only delete your own ads', 'error')
        return redirect(url_for('dashboard'))
    
    # Delete associated image file
    if product.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Ad deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Get similar products (same category, different product)
    similar_products = Product.query.filter(
        and_(
            Product.category == product.category,
            Product.id != product.id,
            Product.is_available == True
        )
    ).limit(4).all()
    
    return render_template('product_detail.html', 
                         product=product, 
                         similar_products=similar_products)

@app.route('/contact_seller/<int:product_id>', methods=['GET', 'POST'])
def contact_seller(product_id):
    product = Product.query.get_or_404(product_id)
    form = MessageForm()
    
    if form.validate_on_submit():
        # Create message
        message = Message(
            content=form.content.data,
            sender_name=form.sender_name.data,
            sender_email=form.sender_email.data,
            sender_phone=form.sender_phone.data,
            product_id=product_id,
            recipient_id=product.user_id,
            sender_id=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(message)
        db.session.commit()
        
        flash('Message sent successfully! The seller will contact you soon.', 'success')
        return redirect(url_for('product_detail', product_id=product_id))
    
    return render_template('contact_seller.html', form=form, product=product)

@app.route('/messages')
@login_required
def messages():
    # Get received messages
    received_messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    # Mark messages as read
    Message.query.filter_by(recipient_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return render_template('messages.html', messages=received_messages)

@app.route('/search')
def search():
    search_form = SearchForm()
    products = []
    
    if request.args.get('query') or request.args.get('category'):
        # Get query parameters
        query = request.args.get('query', '')
        category = request.args.get('category', '')
        location = request.args.get('location', '')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
        # Build search query
        products_query = Product.query.filter(Product.is_available == True)
        
        if query:
            products_query = products_query.filter(
                or_(
                    Product.title.contains(query),
                    Product.description.contains(query)
                )
            )
        
        if category:
            products_query = products_query.filter(Product.category == category)
        
        if location:
            products_query = products_query.filter(Product.location.contains(location))
        
        if min_price is not None:
            products_query = products_query.filter(Product.price >= min_price)
        
        if max_price is not None:
            products_query = products_query.filter(Product.price <= max_price)
        
        products = products_query.order_by(Product.created_at.desc()).all()
    
    return render_template('search.html', 
                         products=products, 
                         search_form=search_form,
                         categories=CATEGORIES)

@app.route('/category/<category_name>')
def category_products(category_name):
    if category_name not in CATEGORIES:
        flash('Category not found', 'error')
        return redirect(url_for('index'))
    
    products = Product.query.filter_by(category=category_name, is_available=True).order_by(Product.created_at.desc()).all()
    
    return render_template('search.html', 
                         products=products, 
                         category_name=category_name,
                         categories=CATEGORIES)

@app.route('/order/<int:product_id>', methods=['GET', 'POST'])
def place_order(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product is available
    if not product.is_available:
        flash('This product is no longer available', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Check if user is trying to buy their own product
    if current_user.is_authenticated and current_user.id == product.user_id:
        flash('You cannot order your own product', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    form = OrderForm()
    
    if form.validate_on_submit():
        # Generate order number
        order = Order()
        order.order_number = Order.generate_order_number()
        
        # Set order details
        order.buyer_name = form.buyer_name.data
        order.buyer_email = form.buyer_email.data
        order.buyer_phone = form.buyer_phone.data
        order.buyer_address = form.buyer_address.data
        order.total_amount = product.price
        order.payment_method = form.payment_method.data
        order.notes = form.notes.data
        order.product_id = product_id
        order.seller_id = product.user_id
        
        if current_user.is_authenticated:
            order.buyer_id = current_user.id
        
        db.session.add(order)
        
        # Mark product as sold
        product.is_available = False
        
        db.session.commit()
        
        flash('Order placed successfully! The seller will contact you soon.', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    return render_template('place_order.html', form=form, product=product)

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('order_confirmation.html', order=order)

@app.route('/orders')
@login_required
def my_orders():
    # Get orders as buyer
    buyer_orders = Order.query.filter_by(buyer_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    # Get orders as seller
    seller_orders = Order.query.filter_by(seller_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    return render_template('my_orders.html', buyer_orders=buyer_orders, seller_orders=seller_orders)

@app.route('/order/<int:order_id>/update_status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Check if user is the seller
    if order.seller_id != current_user.id:
        flash('You are not authorized to update this order', 'error')
        return redirect(url_for('my_orders'))
    
    new_status = request.form.get('status')
    if new_status in ['pending', 'confirmed', 'completed', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Order status updated to {new_status}', 'success')
    else:
        flash('Invalid status', 'error')
    
    return redirect(url_for('my_orders'))

@app.route('/bill/<int:order_id>')
def generate_bill(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Check if user is buyer or seller
    if current_user.is_authenticated:
        if current_user.id not in [order.buyer_id, order.seller_id]:
            flash('You are not authorized to view this bill', 'error')
            return redirect(url_for('index'))
    else:
        # For non-authenticated users, we'll allow access but this could be restricted
        pass
    
    return render_template('bill.html', order=order)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
