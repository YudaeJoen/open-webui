import os
import requests
import time

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
AGENT_ID = "1b915c4a-8eb8-4fe4-a508-9feb5f9bbc48"

def monitor_agent():
    while True:
        r = requests.get(f"http://localhost:3000/api/v1/agents/{AGENT_ID}", 
                        headers={"Authorization": f"Bearer {API_KEY}"})
        data = r.json()
        status = data.get("status")
        current_step = data.get("current_step")
        
        print(f"Status: {status}, Step: {current_step}")
        
        if status == "completed":
            print("\n=== Agent Completed ===")
            artifacts = data.get("artifacts", {})
            final_review = artifacts.get("final_review", {})
            if final_review:
                print(f"Quality: {final_review.get('quality_assessment', 'N/A')}")
            break
        elif status == "failed":
            print("\n=== Agent Failed ===")
            print(data.get("error", "Unknown error"))
            break
        
        time.sleep(5)

if __name__ == "__main__":
    monitor_agent()
