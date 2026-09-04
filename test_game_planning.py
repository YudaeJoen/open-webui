import os
import requests
import time
import json

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1/agents"

def create_game_design_agent():
    """게임 기획 에이전트 생성"""
    url = f"{BASE_URL}/quick/game-design"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "game_concept": "간단한 2D 점프 게임",
        "genre": "캐주얼",
        "target_platform": "모바일"
    }
    
    print("게임 기획 에이전트 생성 요청 중...")
    print(f"데이터: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n[OK] 에이전트 생성 성공!")
        print(f"에이전트 ID: {result.get('id')}")
        print(f"이름: {result.get('name')}")
        print(f"상태: {result.get('status')}")
        return result.get('id')
    else:
        print(f"\n[ERROR] 에이전트 생성 실패 (상태 코드: {response.status_code})")
        print(response.text)
        return None

def monitor_agent(agent_id, max_wait=120):
    """에이전트 상태 모니터링"""
    url = f"{BASE_URL}/{agent_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    print(f"\n에이전트 상태 모니터링 시작 (최대 {max_wait}초)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            agent = response.json()
            status = agent.get('status')
            current_step = agent.get('current_step')
            
            print(f"\n상태: {status}, 현재 단계: {current_step}")
            
            if status in ['completed', 'failed']:
                return agent
            
            time.sleep(5)
        else:
            print(f"[ERROR] 상태 조회 실패: {response.status_code}")
            return None
    
    print("[WARN] 시간 초과")
    return None

def check_artifacts(agent):
    """결과물 확인"""
    artifacts = agent.get('artifacts', {})
    
    print("\n" + "=" * 60)
    print("생성된 결과물")
    print("=" * 60)
    
    if not artifacts:
        print("[WARN] 생성된 결과물이 없습니다.")
        return False
    
    for key, value in artifacts.items():
        print(f"\n{key}:")
        if isinstance(value, str):
            print(f"  타입: 문자열")
            print(f"  길이: {len(value)}자")
            print(f"\n내용 미리보기:")
            print("-" * 40)
            preview = value[:500] if len(value) > 500 else value
            print(preview)
            if len(value) > 500:
                print(f"\n... (총 {len(value)}자)")
            print("-" * 40)
        elif isinstance(value, list):
            print(f"  타입: 리스트")
            print(f"  개수: {len(value)}개")
            if value and isinstance(value[0], str):
                print(f"\n첫 번째 항목 미리보기:")
                print("-" * 40)
                preview = value[0][:500] if len(value[0]) > 500 else value[0]
                print(preview)
                print("-" * 40)
        else:
            print(f"  타입: {type(value).__name__}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("게임 기획 에이전트 테스트")
    print("=" * 60)
    
    agent_id = create_game_design_agent()
    
    if agent_id:
        agent = monitor_agent(agent_id)
        
        if agent:
            print(f"\n최종 상태: {agent.get('status')}")
            
            if agent.get('status') == 'completed':
                print("\n[OK] 에이전트 실행 완료!")
                check_artifacts(agent)
            else:
                print("\n[ERROR] 에이전트 실행 실패")
                
                history = agent.get('execution_history', [])
                if history:
                    print("\n실행 이력:")
                    for step in history:
                        print(f"  - {step.get('step_id')}: {step.get('status')}")
                        if step.get('error'):
                            print(f"    에러: {step.get('error')}")
