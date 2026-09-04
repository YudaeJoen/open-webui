import os
import requests
import time
import json
from requests.exceptions import RequestException, ConnectionError, Timeout

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
AGENT_ID = "7470f01d-7415-4276-88cd-a6d213c60a0a"
BASE_URL = "http://localhost:3000/api/v1"

def check_server_health(max_retries=2):
    for attempt in range(max_retries):
        try:
            r = requests.get(
                f"{BASE_URL}/models",
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=(5, 10)
            )
            if r.status_code == 200:
                return True
        except (ConnectionError, Timeout) as e:
            if attempt < max_retries - 1:
                time.sleep(1 ** (attempt + 1))
        except Exception as e:
            pass
    return False

def get_agent_status(max_retries=5):
    for attempt in range(max_retries):
        try:
            r = requests.get(
                f"{BASE_URL}/agents/{AGENT_ID}",
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=(10, 30)
            )
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                print(f"\n[ERROR] Agent not found (404)")
                return None
            elif r.status_code == 401:
                print(f"\n[ERROR] Unauthorized - check API key")
                return None
            else:
                print(f"\n[ERROR] HTTP {r.status_code}: {r.text[:200]}")
                return None
        except ConnectionError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"\n[WARN] Connection failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"\n[ERROR] Connection failed after {max_retries} attempts")
                return None
        except Timeout as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"\n[WARN] Request timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"\n[ERROR] Request timeout after {max_retries} attempts")
                return None
        except RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"\n[WARN] Request error (attempt {attempt + 1}/{max_retries}): {e}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"\n[ERROR] Request error after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return None
    return None

def print_step_details(step):
    print(f"\nStep: {step.get('name')}")
    print(f"Status: {step.get('status')}")
    print(f"Result preview: {str(step.get('result', ''))[:200]}...")

def print_progress_bar(current, total, bar_length=40):
    if total == 0:
        progress = 0
    else:
        progress = current / total
    
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f'[{bar}] {current}/{total} ({int(progress * 100)}%)'

def get_plan_steps_status(plan_data):
    steps = plan_data.get('steps', [])
    status_count = {
        'pending': 0,
        'in_progress': 0,
        'completed': 0,
        'failed': 0
    }
    
    for step in steps:
        status = step.get('status', 'pending')
        if status in status_count:
            status_count[status] += 1
    
    return status_count

print("=" * 70)
print("Agent Monitoring (Improved)")
print("=" * 70)
print("Press Ctrl+C to stop\n")

last_status = None
last_current_step = None
consecutive_failures = 0
max_consecutive_failures = 10

try:
    while True:
        data = get_agent_status()
        
        if data is None:
            consecutive_failures += 1
            
            if consecutive_failures >= max_consecutive_failures:
                print(f"\n[ERROR] Too many consecutive failures ({consecutive_failures}), stopping...")
                break
            
            print(f"\r[{time.strftime('%H:%M:%S')}] Connection lost, retrying... ({consecutive_failures}/{max_consecutive_failures})", end='', flush=True)
            time.sleep(5)
            
            if consecutive_failures == 3:
                print(f"\n[{time.strftime('%H:%M:%S')}] Checking server health...")
                if check_server_health():
                    print(f"[{time.strftime('%H:%M:%S')}] Server is up, retrying...")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Server appears to be down, waiting...")
            
            continue
        else:
            consecutive_failures = 0
        
        status = data.get('status')
        current_step = data.get('current_step')
        
        # 에이전트 상태가 변경되면 상세 정보 출력
        if status != last_status or current_step != last_current_step:
            print(f"\n[{time.strftime('%H:%M:%S')}] Status: {status.upper()}")
            
            if current_step:
                print(f"Current Step: {current_step}")
            
            # 계획 스텝 상태 확인
            plan_data = data.get('plan', {})
            if plan_data:
                steps = plan_data.get('steps', [])
                if steps:
                    status_count = get_plan_steps_status(plan_data)
                    print(f"Plan Steps: {status_count['pending']} pending, {status_count['in_progress']} in progress, {status_count['completed']} completed, {status_count['failed']} failed")
                    print(f"Progress: {print_progress_bar(status_count['completed'], len(steps))}")
            
            # 실행 이력 확인
            execution_history = data.get('execution_history', [])
            completed_steps = [s for s in execution_history if s.get('status') == 'success']
            failed_steps = [s for s in execution_history if s.get('status') == 'failed']
            
            print(f"Execution History: {len(completed_steps)} completed, {len(failed_steps)} failed")
            
            last_status = status
            last_current_step = current_step
        
        # 완료 또는 실패 상태면 상세 결과 출력
        if status in ['completed', 'failed']:
            print(f"\n{'=' * 70}")
            print(f"Agent {status.upper()}")
            print(f"{'=' * 70}")
            
            print(f"\nTotal Steps: {len(data.get('execution_history', []))}")
            
            # 각 스텝 상세 정보
            for i, step in enumerate(data.get('execution_history', []), 1):
                print(f"\nStep {i}:")
                print_step_details(step)
            
            # 결과물 출력
            artifacts = data.get('artifacts', {})
            final_review = artifacts.get('final_review', {})
            
            if final_review:
                print("\n" + "=" * 70)
                print("Final Review (Improved Prompts)")
                print("=" * 70)
                print(f"Quality Assessment: {final_review.get('quality_assessment', 'N/A')}")
                
                strengths = final_review.get('strengths', [])
                if strengths:
                    print(f"\nStrengths ({len(strengths)}):")
                    for i, s in enumerate(strengths, 1):
                        print(f"  {i}. {s}")
                
                weaknesses = final_review.get('weaknesses', [])
                if weaknesses:
                    print(f"\nWeaknesses ({len(weaknesses)}):")
                    for i, w in enumerate(weaknesses, 1):
                        print(f"  {i}. {w}")
                
                recommendations = final_review.get('recommendations', [])
                if recommendations:
                    print(f"\nRecommendations ({len(recommendations)}):")
                    for i, r in enumerate(recommendations[:5], 1):
                        print(f"  {i}. {r[:100]}...")
                
                print(f"\nCompletion Status: {final_review.get('completion_status', 'N/A')}")
                
                # 다음 단계가 있으면 출력
                next_steps = final_review.get('next_steps', [])
                if next_steps:
                    print(f"\nNext Steps ({len(next_steps)}):")
                    for i, ns in enumerate(next_steps[:3], 1):
                        print(f"  {i}. {ns[:100]}...")
            else:
                print("\nNo final review available yet")
            
            # 모든 계획 스텝 상태 출력
            plan_data = data.get('plan', {})
            if plan_data:
                steps = plan_data.get('steps', [])
                if steps:
                    print("\n" + "=" * 70)
                    print("All Plan Steps Status")
                    print("=" * 70)
                    for step in steps:
                        step_name = step.get('name', 'Unknown')
                        step_status = step.get('status', 'pending')
                        print(f"  - {step_name}: {step_status.upper()}")
            
            break
        
        # 진행 중 상태면 간단히 업데이트
        print(f"\r[{time.strftime('%H:%M:%S')}] Monitoring... (status: {status})", end='', flush=True)
        time.sleep(5)

except KeyboardInterrupt:
    print("\n\nMonitoring stopped by user")
    # 최종 상태 출력
    data = get_agent_status()
    if data:
        print(f"\nFinal Status: {data.get('status')}")
        print(f"Current Step: {data.get('current_step', 'N/A')}")
except Exception as e:
    print(f"\nUnexpected error: {e}")
    import traceback
    traceback.print_exc()
