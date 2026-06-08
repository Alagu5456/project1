import requests
import io

url = 'http://127.0.0.1:5000/detect_condition'

# Create a dummy image in memory
file_content = b'fake image content'
files = {'image': ('test_image.jpg', file_content, 'image/jpeg')}

try:
    print("Sending request to /detect_condition...")
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
