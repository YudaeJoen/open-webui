"""
Test agent execution with auto_execute
"""
import os
import requests
import time
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:3000/api/v1"
API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("Testing Agent Execution")
print("=" * 70)

# Create and auto-execute an agent
print("\n[Step 1] Creating a game design agent with auto_execute=True...")
payload = {
    "name": "Retro Brick Breaker Game",
    "task_type": "game_design",
    "user_request": "Create a retro-style brick breaker game design with power-ups",
    "auto_execute": True
}

try:
    response = requests.post(
        f"{BASE_URL}/agents/",
        json=payload,
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        agent = response.json()
        agent_id = agent.get('id')
        print(f"SUCCESS! Agent created: {agent_id}")
        print(f"Status: {agent.get('status')}")
        print(f"Name: {agent.get('name')}")

        # Monitor agent progress
        print("\n[Step 2] Monitoring agent execution...")
        print("(Press Ctrl+C to stop monitoring)\n")

        last_status = None
        execution_count = 0

        for i in range(60):  # Monitor for up to 60 seconds
            try:
                response = requests.get(
                    f"{BASE_URL}/agents/{agent_id}",
                    headers=headers,
                    timeout=5
                )

                if response.status_code == 200:
                    agent_data = response.json()
                    current_status = agent_data.get('status')
                    current_step = agent_data.get('current_step')
                    execution_history = agent_data.get('execution_history', [])
                    plan = agent_data.get('plan', {})

                    # Print status changes
                    if current_status != last_status:
                        print(f"[{i}s] Status changed: {last_status} -> {current_status}")
                        last_status = current_status

                    # Print plan if it exists
                    if plan and execution_count == 0:
                        print(f"\nPlan created:")
                        steps = plan.get('steps', [])
                        for idx, step in enumerate(steps, 1):
                            print(f"  {idx}. {step.get('name', 'Unknown step')}")

                    # Print current step
                    if current_step:
                        print(f"[{i}s] Current step: {current_step}")

                    # Print execution history changes
                    if len(execution_history) > execution_count:
                        print(f"\nExecution history updated ({len(execution_history)} steps):")
                        for step in execution_history[execution_count:]:
                            step_name = step.get('step_name', 'Unknown')
                            step_status = step.get('status', 'Unknown')
                            print(f"  - {step_name}: {step_status}")
                        execution_count = len(execution_history)

                    # Check if agent finished
                    if current_status in ['completed', 'failed']:
                        print(f"\n{'='*70}")
                        print(f"Agent execution finished with status: {current_status}")
                        print(f"{'='*70}")

                        if current_status == 'completed':
                            artifacts = agent_data.get('artifacts', {})
                            if artifacts:
                                print("\nArtifacts created:")
                                for key, value in artifacts.items():
                                    if isinstance(value, str):
                                        print(f"  {key}: {value[:100]}...")
                                    else:
                                        print(f"  {key}: {value}")

                        break

            except Exception as e:
                print(f"Error checking status: {e}")

            time.sleep(1)
        else:
            print("\nMonitoring timeout reached (60 seconds)")

    else:
        print(f"FAILED to create agent: {response.text}")

except KeyboardInterrupt:
    print("\n\nMonitoring stopped by user")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)
