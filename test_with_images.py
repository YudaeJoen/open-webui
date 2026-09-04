"""
이미지 생성이 포함된 전체 게임 개발 파이프라인 테스트
"""
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
BASE_URL = "http://localhost:3000/api/v1/agents"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("이미지 포함 전체 게임 개발 파이프라인 테스트")
print("=" * 80)

# 전체 개발 파이프라인 실행
data = {
    "game_concept": "간단한 슬라임 키우기 게임. 슬라임을 클릭하면 점수가 올라가고, 점수로 업그레이드를 구매할 수 있습니다.",
    "genre": "아이들 클리커",
    "target_platform": "웹 브라우저",
    "task_type": "full_development"
}

print(f"\n요청 데이터:")
print(json.dumps(data, ensure_ascii=False, indent=2))

try:
    print(f"\n전체 개발 파이프라인 시작...")
    response = requests.post(
        f"{BASE_URL}/quick/full-development",
        headers=headers,
        json=data,
        timeout=300
    )

    if response.status_code == 200:
        result = response.json()
        agent_id = result['id']

        print(f"\n✅ 에이전트 생성 성공!")
        print(f"   ID: {agent_id}")
        print(f"   이름: {result.get('name', 'N/A')}")
        print(f"   상태: {result.get('status', 'N/A')}")

        # 상태 모니터링 (최대 3분)
        print(f"\n진행 상태 모니터링 (최대 180초)...")
        print("(이미지 생성에 시간이 걸릴 수 있습니다)\n")

        for i in range(180):
            time.sleep(1)

            status_response = requests.get(
                f"{BASE_URL}/{agent_id}",
                headers=headers,
                timeout=10
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data.get('status', 'unknown')
                current_step = status_data.get('current_step', 'N/A')
                artifacts = status_data.get('artifacts', {})
                artifact_count = len(artifacts) if artifacts else 0

                # 이미지 개수 확인
                image_count = 0
                for art_val in artifacts.values():
                    if isinstance(art_val, dict) and 'images' in art_val:
                        image_count += len(art_val.get('images', []))

                print(f"   [{i+1}s] {current_status} - {current_step} (결과물: {artifact_count}개, 이미지: {image_count}개)", end='\r')

                if current_status in ['completed', 'failed', 'cancelled']:
                    print()  # 줄바꿈
                    break

        print()

        # 최종 결과 확인
        final_response = requests.get(
            f"{BASE_URL}/{agent_id}",
            headers=headers,
            timeout=10
        )

        if final_response.status_code == 200:
            final_data = final_response.json()

            print(f"\n최종 상태: {final_data.get('status', 'N/A')}")

            artifacts = final_data.get('artifacts', {})
            if artifacts:
                print(f"\n생성된 결과물: {len(artifacts)}개")

                total_images = 0
                for key, art in artifacts.items():
                    if isinstance(art, dict):
                        title = art.get('title', key)
                        images = art.get('images', [])
                        total_images += len(images)

                        print(f"  - {key}: {title}")
                        if images:
                            print(f"    이미지: {len(images)}개")
                            for img in images:
                                print(f"      {img}")

                print(f"\n총 이미지: {total_images}개")

            # HTML 내보내기 제안
            print(f"\n" + "=" * 80)
            print(f"HTML 파일로 결과 내보내기:")
            print(f"python export_agent_html.py {agent_id}")
            print("=" * 80)

    else:
        print(f"\n❌ 실패: HTTP {response.status_code}")
        print(f"응답: {response.text}")

except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()

print()
