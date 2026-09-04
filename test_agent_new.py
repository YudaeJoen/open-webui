import os
import requests
import json
import time

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1"

def create_agent():
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
        "auto_execute": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/agents/",
            json=agent_config,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        
        if response.status_code == 200:
            agent_data = response.json()
            print(f"Agent created successfully!")
            print(f"Agent ID: {agent_data.get('id')}")
            print(f"Agent Name: {agent_data.get('name')}")
            return agent_data
        else:
            print(f"Failed to create agent: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"Error creating agent: {e}")
        return None

def start_agent(agent_id):
    try:
        response = requests.post(
            f"{BASE_URL}/agents/{agent_id}/start",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Agent started successfully!")
            print(f"Status: {result.get('status')}")
            return True
        else:
            print(f"Failed to start agent: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error starting agent: {e}")
        return False

def monitor_agent(agent_id):
    print(f"\n{'=' * 70}")
    print(f"Monitoring Agent: {agent_id}")
    print(f"{'=' * 70}\n")
    
    last_status = None
    start_time = time.time()
    
    while True:
        try:
            response = requests.get(
                f"{BASE_URL}/agents/{agent_id}",
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                current_step = data.get('current_step')
                
                elapsed = int(time.time() - start_time)
                
                if status != last_status:
                    print(f"[{elapsed}s] Status: {status.upper()}")
                    if current_step:
                        print(f"        Current Step: {current_step}")
                    last_status = status
                
                if status in ['completed', 'failed']:
                    print(f"\n{'=' * 70}")
                    print(f"Agent {status.upper()}")
                    print(f"{'=' * 70}")
                    print(f"Total Time: {elapsed}s")
                    
                    artifacts = data.get('artifacts', {})
                    final_review = artifacts.get('final_review', {})
                    
                    if final_review:
                        print(f"\nQuality Assessment: {final_review.get('quality_assessment', 'N/A')}")
                        print(f"Completion Status: {final_review.get('completion_status', 'N/A')}")
                    
                    return data
                else:
                    print(f"\r[{elapsed}s] Monitoring... (status: {status})", end='', flush=True)
                    
            else:
                print(f"\nError: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"\nMonitoring error: {e}")
        
        time.sleep(3)

if __name__ == "__main__":
    print("Creating new agent...")
    agent = create_agent()
    
    if agent:
        agent_id = agent.get('id')
        
        print(f"\nStarting agent execution...")
        if start_agent(agent_id):
            print(f"\nMonitoring started. Press Ctrl+C to stop.\n")
            result = monitor_agent(agent_id)
            
            if result:
                print(f"\n\nAgent execution completed!")
                print(f"Final Status: {result.get('status')}")
        else:
            print("Failed to start agent")
    else:
        print("Failed to create agent")
