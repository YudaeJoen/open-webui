import os
import requests
import time
import json

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1/agents"

def start_agent(agent_id):
    """에이전트 시작"""
    url = f"{BASE_URL}/{agent_id}/start"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    print(f"\nStarting agent {agent_id}...")
    
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] Agent started successfully!")
        print(f"New Status: {result.get('status')}")
        return True
    else:
        print(f"[ERROR] Agent start failed (status code: {response.status_code})")
        print(response.text)
        return False

def create_game_design_agent():
    """게임 기획 에이전트 생성 (영문)"""
    url = f"{BASE_URL}/quick/game-design"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "game_concept": "Simple 2D Jump Game",
        "genre": "Casual",
        "target_platform": "Mobile"
    }
    
    print("Creating game design agent...")
    print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n[OK] Agent created successfully!")
        print(f"Agent ID: {result.get('id')}")
        print(f"Name: {result.get('name')}")
        print(f"Status: {result.get('status')}")
        return result.get('id')
    else:
        print(f"\n[ERROR] Agent creation failed (status code: {response.status_code})")
        print(response.text)
        return None

def monitor_agent(agent_id, max_wait=120):
    """에이전트 상태 모니터링"""
    url = f"{BASE_URL}/{agent_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    print(f"\nMonitoring agent status (max {max_wait} seconds)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            agent = response.json()
            status = agent.get('status')
            current_step = agent.get('current_step')
            
            print(f"\nStatus: {status}, Current Step: {current_step}")
            
            if status in ['completed', 'failed']:
                return agent
            
            time.sleep(5)
        else:
            print(f"[ERROR] Status check failed: {response.status_code}")
            return None
    
    print("[WARN] Timeout")
    return None

def check_artifacts(agent):
    """결과물 확인"""
    artifacts = agent.get('artifacts', {})
    
    print("\n" + "=" * 60)
    print("Generated Artifacts")
    print("=" * 60)
    
    if not artifacts:
        print("[WARN] No artifacts generated.")
        return False
    
    final_review = artifacts.get('final_review', {})
    if final_review:
        print(f"\nQuality Score: {final_review.get('quality_assessment', 'N/A')}")
        print(f"Summary: {final_review.get('summary', 'N/A')[:200]}...")
        
        deliverables = final_review.get('deliverables', [])
        print(f"\nDeliverables ({len(deliverables)} items):")
        for i, d in enumerate(deliverables, 1):
            print(f"  {i}. {d}")
        
        recommendations = final_review.get('recommendations', [])
        if recommendations:
            print(f"\nTop 3 Recommendations:")
            for i, r in enumerate(recommendations[:3], 1):
                print(f"  {i}. {r[:100]}...")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Game Design Agent Test (English)")
    print("=" * 60)
    
    agent_id = create_game_design_agent()
    
    if agent_id:
        if start_agent(agent_id):
            agent = monitor_agent(agent_id)
            
            if agent:
                print(f"\nFinal Status: {agent.get('status')}")
                
                if agent.get('status') == 'completed':
                    print("\n[OK] Agent execution completed!")
                    check_artifacts(agent)
                else:
                    print("\n[ERROR] Agent execution failed")
                    
                    history = agent.get('execution_history', [])
                    if history:
                        print("\nExecution History:")
                        for step in history:
                            print(f"  - {step.get('step_id')}: {step.get('status')}")
                            if step.get('error'):
                                print(f"    Error: {step.get('error')}")
