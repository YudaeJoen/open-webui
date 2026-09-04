import os
import requests
import json
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
AGENT_ID = "24a76e4a-eb12-425f-83a3-d56df5f3fc8a"

r = requests.get(f"http://localhost:3000/api/v1/agents/{AGENT_ID}", 
                headers={"Authorization": f"Bearer {API_KEY}"})
data = r.json()

print("=== 전체 데이터 ===")
print(json.dumps(data, ensure_ascii=False, indent=2))
