import requests
import json

url = 'http://127.0.0.1:5000/predict_price'

# Test Case 1: Mobile
data_mobile = {
    'brand': 'Samsung',
    'category': 'Mobiles',
    'year': 2023,
    'condition': 'Good',
    'original_price': 50000,
    'usage': '1-6 months'
}

# Test Case 2: Furniture
data_furniture = {
    'brand': 'IKEA',
    'category': 'Furniture',
    'year': 2022,
    'condition': 'Good',
    'original_price': 15000,
    'usage': '1-2 years'
}

def test_prediction(data, name):
    print(f"\nTesting {name}...")
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_prediction(data_mobile, "Mobile Phone")
    test_prediction(data_furniture, "Furniture")
