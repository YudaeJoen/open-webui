"""
에이전트 결과물 확인 스크립트
"""
import os
import requests
import json
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

print("=" * 80)
print("에이전트 결과물 확인")
print("=" * 80)

# 모든 에이전트 목록 가져오기
print("\n[1] 완료된 에이전트 목록 조회 중...")
response = requests.get(f"{BASE_URL}/agents/", headers=headers)

if response.status_code == 200:
    agents = response.json()

    # 완료된 에이전트만 필터링
    completed_agents = [a for a in agents if a.get('status') == 'completed']

    if not completed_agents:
        print("완료된 에이전트가 없습니다.")
        sys.exit(0)

    print(f"\n완료된 에이전트: {len(completed_agents)}개\n")

    # 최근 순으로 정렬
    completed_agents.sort(key=lambda x: x.get('created_at', 0), reverse=True)

    # 목록 출력
    for i, agent in enumerate(completed_agents[:10], 1):
        print(f"{i}. {agent.get('name')}")
        print(f"   ID: {agent.get('id')}")
        print(f"   작업 타입: {agent.get('task_type')}")
        print(f"   완료 시간: {agent.get('completed_at', 'N/A')}")
        print()

    # 가장 최근 에이전트 선택
    if len(completed_agents) > 0:
        choice = input(f"\n확인할 에이전트 번호를 입력하세요 (1-{min(10, len(completed_agents))}, Enter=최신): ").strip()

        if choice == "":
            selected_index = 0
        else:
            try:
                selected_index = int(choice) - 1
                if selected_index < 0 or selected_index >= min(10, len(completed_agents)):
                    print("잘못된 번호입니다. 최신 에이전트를 선택합니다.")
                    selected_index = 0
            except ValueError:
                print("잘못된 입력입니다. 최신 에이전트를 선택합니다.")
                selected_index = 0

        selected_agent = completed_agents[selected_index]
        agent_id = selected_agent['id']

        print(f"\n[2] 에이전트 '{selected_agent.get('name')}' 상세 정보 조회 중...")

        # 에이전트 상세 정보 가져오기
        response = requests.get(f"{BASE_URL}/agents/{agent_id}", headers=headers)

        if response.status_code == 200:
            agent_data = response.json()

            print("\n" + "=" * 80)
            print(f"에이전트: {agent_data.get('name')}")
            print("=" * 80)
            print(f"상태: {agent_data.get('status')}")
            print(f"작업 타입: {agent_data.get('task_type')}")
            print(f"사용자 요청: {agent_data.get('user_request')}")
            print()

            # 계획 출력
            plan = agent_data.get('plan', {})
            if plan and plan.get('steps'):
                print("\n" + "-" * 80)
                print("실행 계획:")
                print("-" * 80)
                for step in plan.get('steps', []):
                    status = step.get('status', 'pending')
                    status_icon = {
                        'pending': '⏳',
                        'in_progress': '🔄',
                        'completed': '✅',
                        'failed': '❌'
                    }.get(status, '❓')
                    print(f"{status_icon} {step.get('name', 'Unknown')}: {status}")

            # 산출물 출력
            artifacts = agent_data.get('artifacts', {})
            if artifacts:
                print("\n" + "=" * 80)
                print("생성된 산출물:")
                print("=" * 80)

                for step_key, artifact in artifacts.items():
                    print(f"\n[{step_key}]")
                    print("-" * 80)

                    if isinstance(artifact, dict):
                        # 제목 출력
                        if 'title' in artifact:
                            print(f"\n제목: {artifact['title']}")
                            print()

                        # 내용 출력
                        if 'content' in artifact:
                            content = artifact['content']
                            # 너무 길면 앞부분만 출력
                            if len(content) > 2000:
                                print(content[:2000])
                                print("\n... (내용이 길어 생략됨)")
                                print(f"\n전체 길이: {len(content)} 문자")
                            else:
                                print(content)

                        # 핵심 포인트 출력
                        if 'key_points' in artifact:
                            print("\n핵심 포인트:")
                            for point in artifact['key_points']:
                                print(f"  • {point}")

                        # 다음 단계 출력
                        if 'next_steps' in artifact:
                            print("\n다음 단계:")
                            for step in artifact['next_steps']:
                                print(f"  → {step}")

                        # output 필드가 있는 경우 (step_3 같은 경우)
                        if 'output' in artifact:
                            output = artifact['output']
                            if isinstance(output, dict):
                                if 'title' in output:
                                    print(f"\n제목: {output['title']}")
                                if 'content' in output:
                                    content = output['content']
                                    if len(content) > 2000:
                                        print(content[:2000])
                                        print("\n... (내용이 길어 생략됨)")
                                    else:
                                        print(content)

                    print()

                # 저장 옵션
                save_choice = input("\n결과물을 파일로 저장하시겠습니까? (y/n): ").strip().lower()
                if save_choice == 'y':
                    filename = f"agent_{agent_id}_results.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(agent_data, f, ensure_ascii=False, indent=2)
                    print(f"\n✅ 결과물이 '{filename}' 파일로 저장되었습니다.")

                    # 마크다운 형식으로도 저장
                    md_filename = f"agent_{agent_id}_results.md"
                    with open(md_filename, 'w', encoding='utf-8') as f:
                        f.write(f"# {agent_data.get('name')}\n\n")
                        f.write(f"**작업 타입**: {agent_data.get('task_type')}\n\n")
                        f.write(f"**사용자 요청**: {agent_data.get('user_request')}\n\n")
                        f.write(f"**상태**: {agent_data.get('status')}\n\n")

                        f.write("## 산출물\n\n")
                        for step_key, artifact in artifacts.items():
                            if isinstance(artifact, dict):
                                f.write(f"### {step_key}\n\n")

                                if 'title' in artifact:
                                    f.write(f"**{artifact['title']}**\n\n")

                                if 'content' in artifact:
                                    f.write(f"{artifact['content']}\n\n")

                                if 'output' in artifact and isinstance(artifact['output'], dict):
                                    if 'title' in artifact['output']:
                                        f.write(f"**{artifact['output']['title']}**\n\n")
                                    if 'content' in artifact['output']:
                                        f.write(f"{artifact['output']['content']}\n\n")

                                if 'key_points' in artifact:
                                    f.write("**핵심 포인트:**\n\n")
                                    for point in artifact['key_points']:
                                        f.write(f"- {point}\n")
                                    f.write("\n")

                    print(f"✅ 마크다운 형식으로 '{md_filename}' 파일도 저장되었습니다.")
            else:
                print("\n⚠️  생성된 산출물이 없습니다.")
        else:
            print(f"에이전트 정보를 가져오는데 실패했습니다: {response.status_code}")
else:
    print(f"에이전트 목록을 가져오는데 실패했습니다: {response.status_code}")

print("\n" + "=" * 80)
print("완료")
print("=" * 80)
