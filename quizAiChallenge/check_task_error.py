"""
Check chi tiet loi delivered_failed
"""
import requests
import json

BASE_URL = "https://nonelliptic-dewily-carlos.ngrok-free.dev"
task_id = "7733be2f-6478-48b0-bd3a-509b2b757512"

print("="*70)
print(f"FULL TASK INFO: {task_id}")
print("="*70)

try:
    res = requests.get(f"{BASE_URL}/task/{task_id}", timeout=10)
    data = res.json()
    
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("CHI TIET LOI:")
    print("="*70)
    
    if 'error' in data:
        print(f"Error: {data['error']}")
    
    if 'traceback' in data:
        print(f"Traceback:\n{data['traceback']}")
    
    if 'exc_info' in data:
        print(f"Exception:\n{data['exc_info']}")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70)
