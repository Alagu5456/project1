from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo
from models import CATEGORIES, CONDITIONS

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ProductForm(FlaskForm):
    title = StringField('Product Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField('Category', choices=[(cat, cat) for cat in CATEGORIES], validators=[DataRequired()])
    condition = SelectField('Condition', choices=[(cond, cond) for cond in CONDITIONS], validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    
    # Fields for Price Prediction
    brand = StringField('Brand', validators=[DataRequired(), Length(max=50)])
    purchase_year = FloatField('Purchase Year', validators=[DataRequired(), NumberRange(min=1990, max=2026)])
    usage_duration = SelectField('Usage Duration', 
                               choices=[('Less than 1 month', 'Less than 1 month'),
                                        ('1-6 months', '1-6 months'),
                                        ('6-12 months', '6-12 months'),
                                        ('1-2 years', '1-2 years'),
                                        ('More than 2 years', 'More than 2 years')],
                               validators=[DataRequired()])
    original_price = FloatField('Original Price', validators=[DataRequired(), NumberRange(min=0)])
    
    submit = SubmitField('Post Ad')

class MessageForm(FlaskForm):
    sender_name = StringField('Your Name', validators=[DataRequired(), Length(min=2, max=100)])
    sender_email = StringField('Your Email', validators=[DataRequired(), Email()])
    sender_phone = StringField('Your Phone', validators=[Length(max=20)])
    content = TextAreaField('Message', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Send Message')

class SearchForm(FlaskForm):
    query = StringField('Search products...')
    category = SelectField('Category', choices=[('', 'All Categories')] + [(cat, cat) for cat in CATEGORIES])
    location = StringField('Location')
    min_price = FloatField('Min Price', validators=[NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[NumberRange(min=0)])
    submit = SubmitField('Search')

class OrderForm(FlaskForm):
    buyer_name = StringField('Your Name', validators=[DataRequired(), Length(min=2, max=100)])
    buyer_email = StringField('Your Email', validators=[DataRequired(), Email()])
    buyer_phone = StringField('Your Phone', validators=[DataRequired(), Length(min=10, max=20)])
    buyer_address = TextAreaField('Your Address', validators=[DataRequired(), Length(min=10)])
    payment_method = SelectField('Payment Method', 
                                choices=[('cash', 'Cash on Delivery'), 
                                        ('online', 'Online Payment'), 
                                        ('bank_transfer', 'Bank Transfer')], 
                                validators=[DataRequired()])
    notes = TextAreaField('Additional Notes (Optional)')
    submit = SubmitField('Place Order')
