"""
전체 게임 개발 파이프라인 테스트

이 스크립트는 다음을 테스트합니다:
1. 게임 기획서 작성
2. Stable Diffusion을 사용한 이미지 생성
3. 게임 프로그래밍 코드 생성
"""
import os
import requests
import time
import sys
import io
import json

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:3000/api/v1"
API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("전체 게임 개발 파이프라인 테스트")
print("=" * 80)

# 먼저 이미지 생성 설정 확인
print("\n[Step 0] 이미지 생성 설정 확인...")
try:
    response = requests.get(f"{BASE_URL}/images/config", headers=headers, timeout=10)
    if response.status_code == 200:
        config = response.json()
        print(f"이미지 생성 활성화: {config.get('enabled')}")
        print(f"이미지 생성 엔진: {config.get('engine')}")
        print(f"Automatic1111 URL: {config.get('automatic1111', {}).get('AUTOMATIC1111_BASE_URL')}")

        if not config.get('enabled'):
            print("\n⚠️  경고: 이미지 생성이 비활성화되어 있습니다.")
            print("테스트는 계속되지만 이미지는 생성되지 않을 수 있습니다.")
    else:
        print(f"설정 확인 실패: {response.status_code}")
except Exception as e:
    print(f"설정 확인 오류: {e}")

# 테스트 1: 간단한 게임 기획만 (GAME_DESIGN)
print("\n" + "=" * 80)
print("[Test 1] 게임 기획서 작성만 (GAME_DESIGN)")
print("=" * 80)

payload1 = {
    "name": "Simple Space Shooter Design",
    "task_type": "game_design",
    "user_request": "Create a simple 2D space shooter game design with player ship, enemies, and power-ups",
    "auto_execute": True
}

try:
    response = requests.post(
        f"{BASE_URL}/agents/",
        json=payload1,
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        agent1 = response.json()
        agent1_id = agent1.get('id')
        print(f"✅ Agent 1 생성 성공: {agent1_id}")
        print(f"   이름: {agent1.get('name')}")
        print(f"   작업 타입: {agent1.get('task_type')}")

        # 잠시 대기 후 상태 확인
        print("\n   진행 상태 모니터링 (30초)...")
        for i in range(30):
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/agents/{agent1_id}", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                current_step = data.get('current_step', '')

                if status in ['completed', 'failed']:
                    print(f"\n   최종 상태: {status}")
                    if status == 'completed':
                        artifacts = data.get('artifacts', {})
                        print(f"   생성된 결과물: {len(artifacts)}개")
                    break
                else:
                    print(f"   [{i+1}s] {status} - {current_step}", end='\r')
        print()
    else:
        print(f"❌ 실패: {response.text}")
        agent1_id = None
except Exception as e:
    print(f"❌ 오류: {e}")
    agent1_id = None

# 테스트 2: 전체 개발 파이프라인 (FULL_DEVELOPMENT)
print("\n" + "=" * 80)
print("[Test 2] 전체 게임 개발 파이프라인 (FULL_DEVELOPMENT)")
print("=" * 80)

payload2 = {
    "name": "Complete Puzzle Game Development",
    "task_type": "full_development",
    "user_request": "Create a complete match-3 puzzle game with colorful gems, particle effects, and progressive difficulty",
    "auto_execute": True
}

try:
    response = requests.post(
        f"{BASE_URL}/agents/",
        json=payload2,
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        agent2 = response.json()
        agent2_id = agent2.get('id')
        print(f"✅ Agent 2 생성 성공: {agent2_id}")
        print(f"   이름: {agent2.get('name')}")
        print(f"   작업 타입: {agent2.get('task_type')}")

        # 더 긴 시간동안 모니터링 (이미지 생성 포함)
        print("\n   진행 상태 모니터링 (최대 120초)...")
        print("   (이미지 생성은 시간이 걸릴 수 있습니다)")

        last_step = ""
        for i in range(120):
            time.sleep(1)
            try:
                response = requests.get(f"{BASE_URL}/agents/{agent2_id}", headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    current_step = data.get('current_step', '')

                    # 스텝이 변경되면 출력
                    if current_step != last_step:
                        print(f"\n   [{i+1}s] {status} - {current_step}")
                        last_step = current_step
                    else:
                        print(f"   [{i+1}s] {status} - {current_step}", end='\r')

                    if status in ['completed', 'failed']:
                        print(f"\n\n   최종 상태: {status}")
                        if status == 'completed':
                            artifacts = data.get('artifacts', {})
                            print(f"   생성된 결과물: {len(artifacts)}개")

                            # 결과물 요약 출력
                            print("\n   결과물 목록:")
                            for key in artifacts.keys():
                                print(f"      - {key}")
                        break
            except Exception as e:
                print(f"\n   상태 확인 오류: {e}")
        print()
    else:
        print(f"❌ 실패: {response.text}")
        agent2_id = None
except Exception as e:
    print(f"❌ 오류: {e}")
    agent2_id = None

# 결과 요약
print("\n" + "=" * 80)
print("테스트 결과 요약")
print("=" * 80)

if agent1_id:
    print(f"\n[Test 1] 게임 기획서 작성")
    print(f"  Agent ID: {agent1_id}")
    try:
        response = requests.get(f"{BASE_URL}/agents/{agent1_id}", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  상태: {data.get('status')}")
            artifacts = data.get('artifacts', {})
            print(f"  결과물: {len(artifacts)}개")
    except:
        pass

if agent2_id:
    print(f"\n[Test 2] 전체 개발 파이프라인")
    print(f"  Agent ID: {agent2_id}")
    try:
        response = requests.get(f"{BASE_URL}/agents/{agent2_id}", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  상태: {data.get('status')}")
            artifacts = data.get('artifacts', {})
            print(f"  결과물: {len(artifacts)}개")

            # 저장 옵션
            if artifacts:
                save = input("\n  결과를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"agent_{agent2_id}_full_pipeline.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"  ✅ '{filename}'로 저장되었습니다.")
    except Exception as e:
        print(f"  오류: {e}")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
