"""
간단한 게임 기획서만 테스트
"""
import os
import sys
import io
import requests
import json
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 간단한 게임 기획 요청
data = {
    "game_concept": "Simple Puzzle Game",
    "genre": "Puzzle",
    "target_platform": "Web"
}

print("=" * 80)
print("게임 기획서 생성 테스트")
print("=" * 80)

try:
    response = requests.post(
        f"{BASE_URL}/agents/quick/game-design",
        headers=headers,
        json=data,
        timeout=30
    )

    print(f"응답 상태: {response.status_code}")

    if response.status_code == 200:
        agent = response.json()
        agent_id = agent['id']

        print(f"✅ 에이전트 생성 성공!")
        print(f"Agent ID: {agent_id}")
        print(f"상태: {agent['status']}")
        print(f"작업 타입: {agent['task_type']}")

        # 완료될 때까지 대기
        print("\n진행 상황 모니터링...")
        for i in range(60):  # 최대 60초 대기
            time.sleep(2)

            status_response = requests.get(
                f"{BASE_URL}/agents/{agent_id}",
                headers=headers,
                timeout=10
            )

            if status_response.status_code == 200:
                agent_data = status_response.json()
                status = agent_data['status']
                current_step = agent_data.get('current_step', 'N/A')

                print(f"[{i*2}초] 상태: {status}, 현재 단계: {current_step}")

                if status in ['COMPLETED', 'FAILED']:
                    print(f"\n최종 상태: {status}")

                    # artifacts 확인
                    artifacts = agent_data.get('artifacts', {})
                    print(f"\n결과물: {len(artifacts)}개")

                    for key, value in artifacts.items():
                        print(f"\n{key}:")
                        if isinstance(value, dict):
                            print(f"  키 목록: {list(value.keys())}")
                            if 'title' in value:
                                print(f"  ✅ title: {value['title']}")
                            else:
                                print(f"  ❌ title 없음!")
                    break
    else:
        print(f"❌ 실패: HTTP {response.status_code}")
        print(f"응답: {response.text}")

except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)
