"""
Test polling cho task da tao
"""
import requests
import json
import time

BASE_URL = "https://nonelliptic-dewily-carlos.ngrok-free.dev"

# Task ID tu lan test truoc
task_id = "7733be2f-6478-48b0-bd3a-509b2b757512"

print("="*70)
print(f"POLLING TASK: {task_id}")
print("="*70)

for poll in range(1, 31):  # Poll 30 lan, 1 phut
    try:
        res = requests.get(f"{BASE_URL}/task/{task_id}", timeout=10)
        data = res.json()
        status = data.get('status')
        
        print(f"[Poll {poll}] {status}")
        
        if status == 'completed':
            print("\n✓ TASK COMPLETED!")
            print("\nFull response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if 'questions' in data:
                print(f"\n✓✓ TAO THANH CONG {len(data['questions'])} CAU HOI!")
            
            break
        
        elif status == 'failed':
            print("\n✗ TASK FAILED!")
            print(f"Error: {data.get('error')}")
            break
        
        time.sleep(2)
    
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*70)
