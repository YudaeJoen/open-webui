"""
step_3의 실제 내용 확인
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
    SELECT artifacts
    FROM agent
    ORDER BY created_at DESC
    LIMIT 1
""")

row = cursor.fetchone()

if row:
    artifacts_json = row[0]
    if artifacts_json:
        artifacts = json.loads(artifacts_json)

        step_3 = artifacts.get('step_3', {})

        print("=" * 80)
        print("step_3 전체 내용:")
        print("=" * 80)
        print(json.dumps(step_3, indent=2, ensure_ascii=False))
        print("=" * 80)

conn.close()
