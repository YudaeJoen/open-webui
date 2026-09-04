"""
에이전트 목록 조회
"""
import os
import sys
import io
import requests
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("에이전트 목록")
print("=" * 80)

try:
    response = requests.get(f"{BASE_URL}/agents", headers=headers, timeout=10)

    print(f"응답 상태: {response.status_code}")
    print(f"응답 내용: {response.text[:200]}")

    if response.status_code == 200:
        agents = response.json()

        # 최신순 정렬
        agents_sorted = sorted(agents, key=lambda x: x.get('created_at', ''), reverse=True)

        print(f"\n총 {len(agents_sorted)}개 에이전트\n")

        for idx, agent in enumerate(agents_sorted[:10], 1):
            print(f"{idx}. ID: {agent['id']}")
            print(f"   이름: {agent.get('name', 'N/A')}")
            print(f"   상태: {agent.get('status', 'N/A')}")
            print(f"   작업 타입: {agent.get('task_type', 'N/A')}")
            print(f"   생성: {agent.get('created_at', 'N/A')}")

            # artifacts 확인
            artifacts = agent.get('artifacts', {})
            if artifacts:
                artifact_count = len(artifacts)
                # 이미지 개수 확인
                image_count = 0
                for art_key, art_val in artifacts.items():
                    if isinstance(art_val, dict) and 'images' in art_val:
                        image_count += len(art_val.get('images', []))

                print(f"   결과물: {artifact_count}개 (이미지: {image_count}개)")
            else:
                print(f"   결과물: 0개")
            print()
    else:
        print(f"❌ 실패: HTTP {response.status_code}")
        print(f"응답: {response.text}")

except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)
