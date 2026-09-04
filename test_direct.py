import os
import requests
import json

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3001"

print("Testing agents API directly...")
print(f"Base URL: {BASE_URL}")
print()

# Test 1: Check root endpoint
print("=" * 70)
print("Test 1: GET /")
print("=" * 70)
try:
    response = requests.get(
        f"{BASE_URL}/",
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test 2: Check OpenAPI docs
print("=" * 70)
print("Test 2: GET /openapi.json")
print("=" * 70)
try:
    response = requests.get(
        f"{BASE_URL}/openapi.json",
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get('paths', {})
        agent_paths = {k: v for k, v in paths.items() if 'agent' in k.lower()}
        print(f"Found {len(agent_paths)} agent-related endpoints:")
        for path in sorted(agent_paths.keys()):
            print(f"  - {path}")
            methods = list(agent_paths[path].keys())
            print(f"    Methods: {methods}")
    else:
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test 3: Check agents endpoint
print("=" * 70)
print("Test 3: GET /api/v1/agents")
print("=" * 70)
try:
    response = requests.get(
        f"{BASE_URL}/api/v1/agents",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
