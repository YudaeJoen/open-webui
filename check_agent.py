import os
import requests
import time

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
AGENT_ID = "24a76e4a-eb12-425f-83a3-d56df5f3fc8a"

def check_agent():
    while True:
        r = requests.get(f"http://localhost:3000/api/v1/agents/{AGENT_ID}", 
                        headers={"Authorization": f"Bearer {API_KEY}"})
        data = r.json()
        status = data.get("status")
        artifacts = data.get("artifacts", {})
        
        print(f"상태: {status}")
        
        if status == "completed":
            print("\n=== 에이전트 완료 ===")
            if artifacts:
                print(f"제목: {artifacts.get('title')}")
                print(f"핵심 포인트 개수: {len(artifacts.get('key_points', []))}")
                print(f"다음 단계 개수: {len(artifacts.get('next_steps', []))}")
            break
        elif status == "failed":
            print("\n=== 에이전트 실패 ===")
            print(data.get("error", "알 수 없는 에러"))
            break
        
        time.sleep(5)

if __name__ == "__main__":
    check_agent()
