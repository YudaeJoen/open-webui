"""게임 제작 에이전트 시스템 테스트"""
import os
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1/agents"

def test_game_design():
    """게임 기획서 생성 테스트"""
    print("=" * 60)
    print("게임 기획서 생성 테스트 시작")
    print("=" * 60)
    
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
    
    print(f"\n요청: {url}")
    print(f"데이터: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"\n상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n[OK] 에이전트 생성 성공!")
            print(f"에이전트 ID: {result.get('id')}")
            print(f"이름: {result.get('name')}")
            print(f"상태: {result.get('status')}")
            print(f"작업 유형: {result.get('task_type')}")
            return result.get('id')
        else:
            print(f"\n✗ 에러 발생:")
            print(response.text)
            return None
    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        return None

def get_agent_status(agent_id):
    """에이전트 상태 조회"""
    print("\n" + "=" * 60)
    print(f"에이전트 상태 조회: {agent_id}")
    print("=" * 60)
    
    url = f"{BASE_URL}/{agent_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n상태: {result.get('status')}")
            print(f"현재 단계: {result.get('current_step')}")
            print(f"실행 이력 개수: {len(result.get('execution_history', []))}")
            
            # artifacts 확인
            artifacts = result.get('artifacts', {})
            if artifacts:
                print(f"\n생성된 결과물:")
                for key, value in artifacts.items():
                    print(f"  - {key}: {type(value).__name__}")
            
            return result
        else:
            print(f"\n[ERROR] 에러 발생 (상태 코드: {response.status_code})")
            print(response.text)
            return None
    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        return None

def test_image_generation():
    """이미지 생성 테스트"""
    print("\n" + "=" * 60)
    print("이미지 생성 테스트 시작")
    print("=" * 60)
    
    url = f"{BASE_URL}/quick/image-generation"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "description": "귀여운 게임 캐릭터, 2D 스타일",
        "style": "cartoon",
        "count": 1
    }
    
    print(f"\n요청: {url}")
    print(f"데이터: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"\n상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n[OK] 이미지 생성 에이전트 생성 성공!")
            print(f"에이전트 ID: {result.get('id')}")
            print(f"상태: {result.get('status')}")
            return result.get('id')
        else:
            print(f"\n✗ 에러 발생:")
            print(response.text)
            return None
    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        return None

def list_agents():
    """모든 에이전트 목록 조회"""
    print("\n" + "=" * 60)
    print("에이전트 목록 조회")
    print("=" * 60)
    
    url = BASE_URL + "/"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            agents = response.json()
            print(f"\n총 {len(agents)}개의 에이전트 발견")
            
            for i, agent in enumerate(agents[:5], 1):  # 최대 5개만 출력
                print(f"\n{i}. {agent.get('name')}")
                print(f"   ID: {agent.get('id')}")
                print(f"   상태: {agent.get('status')}")
                print(f"   작업 유형: {agent.get('task_type')}")
                print(f"   생성일: {agent.get('created_at')}")
            
            return agents
        else:
            print(f"\n[ERROR] 에러 발생 (상태 코드: {response.status_code})")
            print(response.text)
            return None
    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        return None


if __name__ == "__main__":
    print("\n[게임 제작 AI 에이전트 시스템 테스트]")
    print("=" * 60)
    
    # 1. 기존 에이전트 목록 조회
    print("\n[1단계] 기존 에이전트 목록 확인")
    list_agents()
    
    # 2. 게임 기획서 생성 테스트
    print("\n[2단계] 게임 기획서 생성 테스트")
    agent_id = test_game_design()
    
    if agent_id:
        # 3. 에이전트 상태 확인
        print("\n[3단계] 에이전트 상태 모니터링")
        time.sleep(2)  # 2초 대기
        get_agent_status(agent_id)
        
        # 4. 5초 후 다시 확인
        print("\n[4단계] 5초 후 재확인")
        time.sleep(5)
        result = get_agent_status(agent_id)
        
        # 5. 최종 결과 출력
        if result:
            print("\n" + "=" * 60)
            print("최종 결과")
            print("=" * 60)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
