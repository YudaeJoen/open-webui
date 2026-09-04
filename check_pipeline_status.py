"""
파이프라인 상태 확인 스크립트
"""
import os
import requests
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:3000/api/v1"
API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("파이프라인 상태 확인")
print("=" * 80)

try:
    # 모든 에이전트 가져오기
    response = requests.get(f"{BASE_URL}/agents/", headers=headers, timeout=10)
    agents = response.json()

    print(f"\n총 {len(agents)}개의 에이전트")
    print()

    # 상태별 분류
    by_status = {}
    for agent in agents:
        status = agent.get('status', 'unknown')
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(agent)

    # 상태별 출력
    for status, agent_list in by_status.items():
        print(f"[{status.upper()}] {len(agent_list)}개")
        for agent in agent_list[:5]:  # 최대 5개만
            print(f"  - {agent.get('name')} (ID: {agent.get('id')[:8]}...)")
            print(f"    작업 타입: {agent.get('task_type')}")
            if status == 'completed':
                artifacts = agent.get('artifacts', {})
                print(f"    결과물: {len(artifacts)}개")
        print()

    # 최근 완료된 에이전트 상세 정보
    completed = [a for a in agents if a.get('status') == 'completed']
    if completed:
        completed.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        latest = completed[0]

        print("=" * 80)
        print("최근 완료된 에이전트 상세 정보")
        print("=" * 80)
        print(f"이름: {latest.get('name')}")
        print(f"ID: {latest.get('id')}")
        print(f"작업 타입: {latest.get('task_type')}")
        print(f"사용자 요청: {latest.get('user_request')}")
        print()

        # 계획 단계 확인
        plan = latest.get('plan', {})
        if plan and plan.get('steps'):
            print("실행 계획:")
            for step in plan.get('steps', []):
                status_icon = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(step.get('status', 'pending'), '❓')
                print(f"  {status_icon} {step.get('name')}")
            print()

        # 결과물 확인
        artifacts = latest.get('artifacts', {})
        if artifacts:
            print(f"생성된 결과물 ({len(artifacts)}개):")
            for key in artifacts.keys():
                print(f"  - {key}")
            print()

            # 이미지가 생성되었는지 확인
            has_images = any('images' in artifact for artifact in artifacts.values() if isinstance(artifact, dict))
            if has_images:
                print("✅ 이미지가 생성되었습니다!")
                for key, artifact in artifacts.items():
                    if isinstance(artifact, dict) and 'images' in artifact:
                        images = artifact.get('images', [])
                        print(f"  {key}: {len(images)}개 이미지")
                        for img_url in images:
                            print(f"    - {img_url}")
                print()

            # 코드가 생성되었는지 확인
            has_code = any('code' in artifact for artifact in artifacts.values() if isinstance(artifact, dict))
            if has_code:
                print("✅ 코드가 생성되었습니다!")
                for key, artifact in artifacts.items():
                    if isinstance(artifact, dict) and 'code' in artifact:
                        language = artifact.get('language', 'Unknown')
                        framework = artifact.get('framework', 'Unknown')
                        print(f"  {key}: {language} + {framework}")
                print()

        print()
        print("상세 정보를 보려면:")
        print(f"  python view_agent_results.py")
        print()
        print("결과를 저장하려면:")
        print(f"  python save_agent_results.py")

except Exception as e:
    print(f"오류: {e}")

print()
print("=" * 80)
