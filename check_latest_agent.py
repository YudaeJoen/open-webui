"""
최신 에이전트의 상세 정보 확인
"""
import sys
import io
import sqlite3
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('backend/data/webui.db')
cursor = conn.cursor()

# 가장 최근 에이전트 조회
cursor.execute("""
    SELECT id, name, status, task_type, plan, artifacts, created_at
    FROM agent
    ORDER BY created_at DESC
    LIMIT 1
""")

row = cursor.fetchone()

if row:
    agent_id, name, status, task_type, plan_json, artifacts_json, created_at = row

    print("=" * 80)
    print(f"에이전트 ID: {agent_id}")
    print(f"이름: {name}")
    print(f"상태: {status}")
    print(f"작업 타입: {task_type}")
    print(f"생성 시간: {created_at}")
    print("=" * 80)

    # Plan 정보
    if plan_json:
        plan = json.loads(plan_json)
        print("\n[계획]")
        print(f"목표: {plan.get('goal', 'N/A')}")
        print(f"\n단계 수: {len(plan.get('steps', []))}")
        for step in plan.get('steps', []):
            print(f"  - {step['step_id']}: {step['name']}")

    # Artifacts 정보
    if artifacts_json:
        artifacts = json.loads(artifacts_json)
        print(f"\n[결과물] - 총 {len(artifacts)}개")
        for key, value in artifacts.items():
            print(f"\n{key}:")
            if isinstance(value, dict):
                if 'title' in value:
                    print(f"  제목: {value['title']}")
                if 'description' in value:
                    desc = str(value['description'])[:100]
                    print(f"  설명: {desc}...")
                if 'images' in value:
                    print(f"  이미지: {len(value['images'])}개")
                if 'code' in value:
                    print(f"  코드: 있음 ({len(str(value['code']))} 글자)")
                if 'language' in value:
                    print(f"  언어: {value['language']}")
                if 'framework' in value:
                    print(f"  프레임워크: {value['framework']}")

                # 모든 키 출력
                print(f"  키 목록: {list(value.keys())}")
    else:
        print("\n[결과물] - 없음")

conn.close()
