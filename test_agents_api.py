import os
import requests
import json

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3001/api/v1"

print("Testing agents API...")
print(f"Base URL: {BASE_URL}")
print()

# Test 1: Get all agents
print("=" * 70)
print("Test 1: GET /api/v1/agents")
print("=" * 70)
try:
    response = requests.get(
        f"{BASE_URL}/agents",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        agents = response.json()
        print(f"Found {len(agents)} agents")
        for agent in agents:
            print(f"  - ID: {agent.get('id')}, Name: {agent.get('name')}, Status: {agent.get('status')}")
    else:
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test 2: Create a new agent
print("=" * 70)
print("Test 2: POST /api/v1/agents")
print("=" * 70)
agent_config = {
    "name": "Game Design: Space Shooter Game",
    "description": "Create a comprehensive game design document for a space shooter game",
    "task_type": "game_design",
    "user_request": "Create a comprehensive game design document for a space shooter game. The game should feature player spaceship, enemy waves, power-ups, boss battles, and scoring system. Target platform is mobile devices.",
    "context": {
        "model_id": "gpt-oss:20b",
        "temperature": 0.7,
        "max_tokens": 4000,
        "project_type": "space_shooter",
        "target_platform": "mobile",
        "complexity": "medium"
    },
    "auto_execute": False
}

try:
    response = requests.post(
        f"{BASE_URL}/agents",
        json=agent_config,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        agent = response.json()
        print(f"Agent created successfully!")
        print(f"  ID: {agent.get('id')}")
        print(f"  Name: {agent.get('name')}")
        print(f"  Status: {agent.get('status')}")
        print(f"  Task Type: {agent.get('task_type')}")
        
        agent_id = agent.get('id')
        
        print()
        print("=" * 70)
        print("Test 3: GET /api/v1/agents/{agent_id}")
        print("=" * 70)
        response = requests.get(
            f"{BASE_URL}/agents/{agent_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            agent_detail = response.json()
            print(f"Agent retrieved successfully!")
            print(f"  Name: {agent_detail.get('name')}")
            print(f"  Status: {agent_detail.get('status')}")
            print(f"  Plan: {agent_detail.get('plan')}")
    else:
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 70)
print("Tests completed")
print("=" * 70)
