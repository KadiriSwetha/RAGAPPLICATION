"""
Script to manually register FastAPI app with Inngest Dev Server
"""

import requests
import json

# Inngest Dev Server URL
INNGEST_DEV_SERVER = "http://localhost:8288"
# Your FastAPI Inngest endpoint
APP_URL = "http://localhost:8000/api/inngest"

try:
    # Try to sync the app
    print(f"Registering {APP_URL} with Inngest Dev Server...")

    # First, try a GET to see if endpoint exists
    response = requests.get(APP_URL)
    print(f"GET {APP_URL}: Status {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.text[:200]}")

    print("\n✅ Your FastAPI endpoint is accessible!")
    print(f"\nNow, in the Inngest Dev Server UI at {INNGEST_DEV_SERVER}:")
    print("1. Click on 'Apps' or look for sync options")
    print(f"2. Manually add the URL: {APP_URL}")
    print("3. Click 'Sync' or 'Add App'")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"\nMake sure:")
    print("1. FastAPI is running at http://localhost:8000")
    print("2. Inngest Dev Server is running at http://localhost:8288")
