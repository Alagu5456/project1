import requests
import os
from PIL import Image

BASE_URL = 'http://127.0.0.1:5000'
LOGIN_URL = f'{BASE_URL}/login'
POST_AD_URL = f'{BASE_URL}/post_ad'
DASHBOARD_URL = f'{BASE_URL}/admin/dashboard'

# Create dummy image
def create_dummy_image():
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save('test_image.jpg')
    return 'test_image.jpg'

def verify():
    session = requests.Session()
    
    # 1. Login
    print("Logging in...")
    resp = session.post(LOGIN_URL, data={
        'email': 'admin@example.com',
        'password': 'admin123',
        'csrf_token': '' # CSRF might be an issue if enabled, checking...
        # Flask-WTF usually requires CSRF token. I might need to fetch the form first.
    })
    
    # Fetch login page first to get CSRF token if needed, but for simplicity assuming no strict CSRF or handling broadly.
    # Actually, Flask-WTF validates_on_submit handles CSRF. I need to scrape it.
    # Let's try to bypass or scrape.
    
    # Simpler approach: Use app context to test logic directly without HTTP requests overhead for CSRF?
    # No, integration test is better.
    
    # Let's just create a new product directly in DB to test hashing logic? 
    # No, I want to test the full flow including the "Warning" flash message.
    
    # OK, let's try to grab CSRF token.
    login_page = session.get(LOGIN_URL)
    if 'csrf_token' in login_page.text:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        print("Got CSRF token.")
        
        resp = session.post(LOGIN_URL, data={
            'email': 'admin@example.com',
            'password': 'admin123',
            'csrf_token': csrf_token
        })
    else:
        print("No CSRF token found, trying direct login...")
        resp = session.post(LOGIN_URL, data={
            'email': 'admin@example.com',
            'password': 'admin123'
        })
        
    if 'Login successful' in resp.text or 'Dashboard' in resp.text or resp.url == f'{BASE_URL}/':
         print("Login successful.")
    else:
         # It might redirect.
         pass

    # 2. Post Ad 1
    print("Posting Ad 1...")
    img_path = create_dummy_image()
    
    # Get CSRF for post ad
    post_page = session.get(POST_AD_URL)
    csrf_token = ''
    if 'csrf_token' in post_page.text:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(post_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

    files = {'image': open(img_path, 'rb')}
    data = {
        'title': 'Test Product 1',
        'description': 'Description',
        'price': 100,
        'category': 'Mobiles',
        'condition': 'New',
        'location': 'Test Loc',
        'csrf_token': csrf_token,
        'brand': 'Samsung',
        'purchase_year': 2022,
        'usage_duration': '1-2 years',
        'original_price': 1000
    }
    
    resp = session.post(POST_AD_URL, data=data, files=files)
    if 'Your ad has been posted successfully' in resp.text:
        print("Ad 1 Posted.")
    else:
        print("Ad 1 Failed or Redirected.")

    # 3. Post Ad 2 (Duplicate)
    print("Posting Ad 2 (Duplicate)...")
    files = {'image': open(img_path, 'rb')} # Re-open file
    
    # Refresh CSRF
    post_page = session.get(POST_AD_URL)
    if 'csrf_token' in post_page.text:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(post_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        data['csrf_token'] = csrf_token

    data['title'] = 'Test Product 2'
    resp = session.post(POST_AD_URL, data=data, files=files)
    
    # Check for warning
    if 'Warning: This image has been detected' in resp.text:
        print("SUCCESS: Duplicate warning detected!")
    else:
        print("FAIL: No duplicate warning found.")
        # print(resp.text) # Debug

    # 4. Check Admin Dashboard
    print("Checking Admin Dashboard...")
    resp = session.get(DASHBOARD_URL)
    if 'Admin Dashboard' in resp.text and 'Fraud Alerts' in resp.text:
        print("SUCCESS: Admin Dashboard accessible and loading.")
        if 'Test Product 2' in resp.text or 'Duplicate Image' in resp.text: # Should list recent alerts
             print("SUCCESS: Fraud alert listed in dashboard.")
    else:
        print("FAIL: Admin Dashboard not accessible.")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"Error: {e}")
