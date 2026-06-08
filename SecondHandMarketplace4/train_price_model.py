import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle
import random

def generate_synthetic_data(num_samples=1000):
    brands = {
        'Mobiles': ['Samsung', 'Apple', 'Redmi', 'OnePlus', 'Vivo', 'Oppo', 'Realme', 'Xiaomi', 'Google', 'Nothing'],
        'Electronics': ['Sony', 'LG', 'Samsung', 'Dell', 'HP', 'Lenovo', 'Asus', 'Acer', 'Apple'],
        'Cars': ['Maruti', 'Hyundai', 'Honda', 'Toyota', 'Tata', 'Mahindra', 'Kia'],
        'Bikes': ['Hero', 'Honda', 'Bajaj', 'TVs', 'Royal Enfield', 'Yamaha'],
        'Furniture': ['IKEA', 'Godrej', 'Nilkamal', 'Urban Ladder', 'Local'],
        'Fashion': ['Nike', 'Adidas', 'Puma', 'Zara', 'H&M', 'Levis'],
        'Services': ['N/A'],
        'Kids': ['FisherPrice', 'Lego', 'Barbie', 'HotWheels'],
        'Books': ['N/A'],
        'Sports': ['Decathlon', 'Yonex', 'Wilson', 'Nivia'],
        'Houses & Apartments': ['N/A'],
        'Other': ['Generic']
    }
    
    conditions = ['New', 'Like New', 'Good', 'Fair', 'Poor']
    # Depreciation factors for conditions
    condition_factors = {
        'New': 0.95,
        'Like New': 0.85,
        'Good': 0.70,
        'Fair': 0.50,
        'Poor': 0.30
    }
    
    data = []
    
    for _ in range(num_samples):
        category = random.choice(list(brands.keys()))
        brand = random.choice(brands[category])
        
        # Base Original Price ranges per category
        if category == 'Mobiles':
            original_price = random.randint(10000, 150000)
            depreciation_rate = 0.25 # high depreciation
        elif category == 'Electronics':
            original_price = random.randint(20000, 200000)
            depreciation_rate = 0.20
        elif category == 'Cars':
            original_price = random.randint(300000, 2000000)
            depreciation_rate = 0.15
        elif category == 'Bikes':
            original_price = random.randint(50000, 300000)
            depreciation_rate = 0.15
        elif category == 'Furniture':
            original_price = random.randint(5000, 50000)
            depreciation_rate = 0.30
        else:
            original_price = random.randint(1000, 20000)
            depreciation_rate = 0.40
            
        age = random.randint(0, 10) # 0 to 10 years
        
        # Approximate usage hours (just a proxy for "how much used")
        usage_hours = age * 365 * 4 # 4 hours a day
        
        condition = random.choices(conditions, weights=[0.1, 0.2, 0.4, 0.2, 0.1])[0]
        
        # Calculate Resale Price
        # Formula: Original * (1 - dep_rate)^age * condition_factor
        
        # Cap age effect slightly so value doesn't go to ~0 too fast for expensive items
        # But generally follow exponential decay
        
        value_after_age = original_price * ((1 - depreciation_rate) ** age)
        resale_price = value_after_age * condition_factors[condition]
        
        # Add some random noise +/- 10%
        noise = random.uniform(0.9, 1.1)
        resale_price *= noise
        
        resale_price = max(resale_price, original_price * 0.1) # Floor at 10%
        
        data.append({
            'brand': brand,
            'category': category,
            'age': age,
            'condition': condition,
            'usage_hours': usage_hours,
            'original_price': original_price,
            'resale_price': int(resale_price)
        })
        
    return pd.DataFrame(data)

def train_model():
    print("Generating synthetic data...")
    df = generate_synthetic_data(2000) 
    # Save for reference
    df.to_csv('synthetic_prices.csv', index=False)
    print("Synthetic data generated and saved.")

    # Preprocessing
    le_brand = LabelEncoder()
    # Fit on all generated brands + "Other" to be safe
    df['brand'] = le_brand.fit_transform(df['brand'])

    le_condition = LabelEncoder()
    df['condition'] = le_condition.fit_transform(df['condition'])
    
    le_category = LabelEncoder()
    df['category'] = le_category.fit_transform(df['category'])

    # Features and Target
    X = df[['brand', 'category', 'age', 'condition', 'usage_hours', 'original_price']]
    y = df['resale_price']

    # Splitting
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Model Training
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # Evaluation
    score = rf_model.score(X_test, y_test)
    print(f"Model R^2 Score: {score}")

    # Save Model and Encoders
    with open('price_prediction_model.pkl', 'wb') as f:
        pickle.dump(rf_model, f)
    
    with open('brand_encoder.pkl', 'wb') as f:
        pickle.dump(le_brand, f)

    with open('condition_encoder.pkl', 'wb') as f:
        pickle.dump(le_condition, f)
        
    with open('category_encoder.pkl', 'wb') as f:
        pickle.dump(le_category, f)

    print("Model and encoders saved successfully.")

if __name__ == "__main__":
    train_model()
