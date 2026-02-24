# ruff: noqa: E402
import requests

url = "http://localhost:8000/api/accounts/login/"
data = {"phone_number": "1234567890", "password": "password123", "tenant_id": 1}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
