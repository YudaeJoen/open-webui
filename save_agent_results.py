import os
import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = os.environ.get("OPEN_WEBUI_API_KEY", "")
headers = {'Authorization': f'Bearer {API_KEY}'}

# Get most recent completed agent
agents = requests.get('http://localhost:3000/api/v1/agents/', headers=headers).json()
completed = [a for a in agents if a.get('status') == 'completed']
completed.sort(key=lambda x: x.get('created_at', 0), reverse=True)

if completed:
    agent_id = completed[0]['id']
    agent = requests.get(f'http://localhost:3000/api/v1/agents/{agent_id}', headers=headers).json()

    # Save JSON
    with open(f'agent_{agent_id}_results.json', 'w', encoding='utf-8') as f:
        json.dump(agent, f, ensure_ascii=False, indent=2)

    # Save Markdown
    with open(f'agent_{agent_id}_results.md', 'w', encoding='utf-8') as f:
        f.write(f"# {agent.get('name')}\n\n")
        f.write(f"**작업 타입**: {agent.get('task_type')}\n\n")
        f.write(f"**사용자 요청**: {agent.get('user_request')}\n\n")
        f.write(f"**상태**: {agent.get('status')}\n\n")

        artifacts = agent.get('artifacts', {})
        for step_key, artifact in artifacts.items():
            f.write(f"\n## {step_key}\n\n")
            if isinstance(artifact, dict):
                if 'title' in artifact:
                    f.write(f"### {artifact['title']}\n\n")
                if 'content' in artifact:
                    f.write(f"{artifact['content']}\n\n")
                if 'output' in artifact and isinstance(artifact['output'], dict):
                    if 'title' in artifact['output']:
                        f.write(f"### {artifact['output']['title']}\n\n")
                    if 'content' in artifact['output']:
                        f.write(f"{artifact['output']['content']}\n\n")

    print('저장 완료!')
    print(f'- agent_{agent_id}_results.json')
    print(f'- agent_{agent_id}_results.md')
    print(f'\n에이전트: {agent.get("name")}')
    print(f'총 {len(artifacts)}개의 산출물이 생성되었습니다.')
else:
    print('완료된 에이전트가 없습니다.')
