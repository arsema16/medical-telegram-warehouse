#!/usr/bin/env python3
"""
Simple API test script.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test all API endpoints."""
    endpoints = [
        ("Root", "/"),
        ("Stats", "/api/messages/stats"),
        ("Top Products", "/api/reports/top-products?limit=5"),
        ("Channel Activity", "/api/channels/tikvahpharma/activity?days=7"),
        ("Search", "/api/search/messages?query=Amox"),
        ("Visual Content", "/api/reports/visual-content"),
        ("Daily Trends", "/api/reports/daily-trends?days=7"),
    ]
    
    print("=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)
    
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"\n✅ {name}:")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"\n❌ {name}: {e}")

if __name__ == "__main__":
    test_endpoints()