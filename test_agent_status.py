import os
import requests
import time

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1/agents"

def check_agent_status(agent_id):
    """에이전트 상태 확인"""
    url = f"{BASE_URL}/{agent_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Agent Status: {result.get('status')}")
            print(f"Current Step: {result.get('current_step')}")
            print(f"Execution History: {len(result.get('execution_history', []))} steps")
            
            history = result.get('execution_history', [])
            if history:
                print("\nExecution History:")
                for i, step in enumerate(history, 1):
                    print(f"  {i}. {step.get('step_id')}: {step.get('status')}")
                    if step.get('error'):
                        print(f"     Error: {step.get('error')}")
            
            artifacts = result.get('artifacts', {})
            if artifacts:
                print("\nArtifacts:")
                for key, value in artifacts.items():
                    print(f"  - {key}: {type(value).__name__}")
            
            return result
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    agent_id = "9078836c-4c37-4d3f-9ec2-6219e15c7ca9"
    print(f"Checking agent status: {agent_id}")
    print("=" * 60)
    check_agent_status(agent_id)
