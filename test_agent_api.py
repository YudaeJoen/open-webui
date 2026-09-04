"""
Test the agent API endpoints
"""
import os
import requests
import json
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API base URL
BASE_URL = "http://localhost:3000/api/v1"
API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")

# Headers with API key
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("Agent API Test")
print("=" * 60)

# Test 1: Create an agent
print("\n[Test 1] Creating a game design agent...")
payload = {
    "name": "Simple Puzzle Game Agent",
    "task_type": "game_design",
    "user_request": "Create a simple puzzle game like Tetris",
    "auto_execute": False
}

try:
    response = requests.post(
        f"{BASE_URL}/agents/",
        json=payload,
        headers=headers,
        timeout=10
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("SUCCESS! Agent created")
        print(f"Agent ID: {data.get('id')}")
        print(f"Status: {data.get('status')}")
        print(f"Name: {data.get('name')}")
        agent_id = data.get('id')
    else:
        print(f"FAILED: {response.text}")
        agent_id = None

except Exception as e:
    print(f"ERROR: {e}")
    agent_id = None

# Test 2: List all agents
print("\n[Test 2] Listing all agents...")
try:
    response = requests.get(
        f"{BASE_URL}/agents/",
        headers=headers,
        timeout=10
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        agents = response.json()
        print(f"SUCCESS! Found {len(agents)} agent(s)")
        for i, agent in enumerate(agents, 1):
            print(f"  {i}. {agent.get('name')} ({agent.get('status')})")
    else:
        print(f"FAILED: {response.text}")

except Exception as e:
    print(f"ERROR: {e}")

# Test 3: Get specific agent
if agent_id:
    print(f"\n[Test 3] Getting agent details for {agent_id}...")
    try:
        response = requests.get(
            f"{BASE_URL}/agents/{agent_id}",
            headers=headers,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS! Agent details:")
            print(f"  Name: {data.get('name')}")
            print(f"  Status: {data.get('status')}")
            print(f"  Task Type: {data.get('task_type')}")
            print(f"  Request: {data.get('user_request')}")
        else:
            print(f"FAILED: {response.text}")

    except Exception as e:
        print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
