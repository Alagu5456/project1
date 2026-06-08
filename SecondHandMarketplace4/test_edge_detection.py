import requests
from io import BytesIO
from PIL import Image
import random

url = 'http://127.0.0.1:5000/detect_condition'

def create_noisy_image():
    # Create an image full of varying pixels (high edges)
    # 200x200 image
    img = Image.new('RGB', (200, 200))
    pixels = img.load()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            # Random noise
            pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def create_smooth_image():
    # Solid bright color (low edges, high brightness)
    img = Image.new('RGB', (200, 200), color=(200, 200, 200)) # Light gray
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_condition(name, img_data, expected=None):
    print(f"\nTesting {name}...")
    files = {'image': ('test.jpg', img_data, 'image/jpeg')}
    try:
        response = requests.post(url, files=files)
        data = response.json()
        print(f"Detected: {data.get('condition')}")
        if expected and data.get('condition') == expected:
            print("PASS")
        elif expected:
             print(f"FAIL (Expected {expected})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("--- Verifying Edge Detection Logic ---")
    
    # 1. Noisy Image (Simulating broken screen / chaos) -> Should detect as Poor
    noisy = create_noisy_image()
    test_condition("High Noise Image (Simulating Cracks)", noisy, expected="Poor")
    
    # 2. Smooth Image (Simulating Good Condition) -> Should detect as New/Good
    smooth = create_smooth_image()
    test_condition("Smooth Image (Simulating Good Condition)", smooth, expected="New")
