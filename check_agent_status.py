import os
import requests

r = requests.get('http://localhost:3000/api/v1/agents/a7d4faec-8225-4190-b613-4779c2ee139f', headers={'Authorization': 'Bearer ' + os.environ.get("OPEN_WEBUI_API_KEY", "")})
data = r.json()
print(f"Status: {data.get('status')}")
print(f"Current Step: {data.get('current_step')}")
print("Steps:")
for s in data.get('plan', {}).get('steps', []):
    print(f"  {s.get('step_id')}: {s.get('status')}")
