import sqlite3
import json

conn = sqlite3.connect('data/webui.db')
cursor = conn.cursor()

cursor.execute('SELECT id, user_id, name, status, current_step, created_at, plan, artifacts FROM agent WHERE id = ?', ('7470f01d-7415-4276-88cd-a6d213c60a0a',))
result = cursor.fetchone()

if result:
    print('Agent ID:', result[0])
    print('User ID:', result[1])
    print('Name:', result[2])
    print('Status:', result[3])
    print('Current Step:', result[4])
    print('Created At:', result[5])
    
    plan = json.loads(result[6]) if result[6] else {}
    steps = plan.get('steps', [])
    print('\nPlan Steps:')
    for step in steps:
        print(f'  - {step.get("step_id", "N/A")} ({step.get("name", "Unknown")}): {step.get("status", "pending")}')
        
    artifacts = json.loads(result[7]) if result[7] else {}
    print(f'\nArtifacts:')
    for key, value in artifacts.items():
        print(f'  - {key}: {str(value)[:100]}...')
            
else:
    print('Agent not found')
    
conn.close()
