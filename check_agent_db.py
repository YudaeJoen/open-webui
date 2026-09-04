import sqlite3

conn = sqlite3.connect('storage/webui.db')
cursor = conn.cursor()

cursor.execute('SELECT id, user_id, name, status, current_step, created_at FROM agents WHERE id = ?', ('7470f01d-7415-4276-88cd-a6d213c60a0a',))
result = cursor.fetchone()

if result:
    print('Agent ID:', result[0])
    print('User ID:', result[1])
    print('Name:', result[2])
    print('Status:', result[3])
    print('Current Step:', result[4])
    print('Created At:', result[5])
    
    cursor.execute('SELECT step_id, name, status FROM agent_plan_steps WHERE agent_id = ?', ('7470f01d-7415-4276-88cd-a6d213c60a0a',))
    steps = cursor.fetchall()
    print('\nPlan Steps:')
    for step in steps:
        print(f'  - {step[0]} ({step[1]}): {step[2]}')
        
    cursor.execute('SELECT COUNT(*) FROM agent_artifacts WHERE agent_id = ?', ('7470f01d-7415-4276-88cd-a6d213c60a0a',))
    artifact_count = cursor.fetchone()[0]
    print(f'\nArtifacts Count: {artifact_count}')
    
    if artifact_count > 0:
        cursor.execute('SELECT step_id, artifact_type, artifact_data FROM agent_artifacts WHERE agent_id = ?', ('7470f01d-7415-4276-88cd-a6d213c60a0a',))
        artifacts = cursor.fetchall()
        print('Artifacts:')
        for art in artifacts:
            print(f'  - Step: {art[0]}, Type: {art[1]}')
            
conn.close()
