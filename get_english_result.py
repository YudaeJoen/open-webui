import os
import requests
import json

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
AGENT_ID = "25d797cd-545a-4632-9067-95ba7590c98f"

r = requests.get(f"http://localhost:8080/api/v1/agents/{AGENT_ID}",
                headers={"Authorization": f"Bearer {API_KEY}"})
data = r.json()

print("=" * 60)
print("English Command Agent Test Result")
print("=" * 60)
print(f"Agent ID: {data.get('id')}")
print(f"Name: {data.get('name')}")
print(f"Status: {data.get('status')}")
print(f"Total Steps: {len(data.get('execution_history', []))}")

artifacts = data.get('artifacts', {})
final_review = artifacts.get('final_review', {})

if final_review:
    print("\n" + "=" * 60)
    print("Final Review")
    print("=" * 60)
    print(f"Quality Score: {final_review.get('quality_assessment', 'N/A')}")
    print(f"\nSummary:")
    print(final_review.get('summary', 'N/A'))
    
    deliverables = final_review.get('deliverables', [])
    print(f"\nDeliverables ({len(deliverables)} items):")
    for i, d in enumerate(deliverables, 1):
        print(f"  {i}. {d}")
    
    recommendations = final_review.get('recommendations', [])
    print(f"\nRecommendations ({len(recommendations)} items):")
    for i, r in enumerate(recommendations[:5], 1):
        print(f"  {i}. {r[:120]}...")
    
    print(f"\nCompletion Status: {final_review.get('completion_status', 'N/A')}")
