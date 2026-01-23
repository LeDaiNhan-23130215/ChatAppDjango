"""
Test ket noi ngrok
"""
import requests
import json

BASE_URL = "https://nonelliptic-dewily-carlos.ngrok-free.dev"

print("="*70)
print("TEST KET NOI NGROK")
print("="*70)

# Test 1: Health check
print("\n[1] Health check...")
try:
    res = requests.get(f"{BASE_URL}/health", timeout=10)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    
    if res.status_code == 200:
        print("✓ NGROK CONNECTED OK")
    else:
        print(f"✗ Health check failed: {res.status_code}")
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
    print("\nKhong the ket noi ngrok!")
    print("Kiem tra:")
    print("- Co chay ngrok khong?")
    print("- URL ngrok con hieu luc khong?")
    print("- Network/firewall co chan khong?")
    exit(1)

# Test 2: Generate request
print("\n[2] Generate request...")
payload = {
    "user_id": 1,
    "quiz_size": 3,
    "declared_level": "Advanced",
    "profession": "engineer",
    "weak_skills": ["grammar"],
    "preferred_topics": ["APIs", "databases"],
    "sync": True
}

print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    res = requests.post(
        f"{BASE_URL}/generate",
        json=payload,
        timeout=30
    )
    print(f"\nStatus: {res.status_code}")
    data = res.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if res.status_code == 202 and "task_id" in data:
        print("✓ GENERATE REQUEST OK")
        task_id = data["task_id"]
        
        # Test 3: Poll for result
        print(f"\n[3] Polling task {task_id}...")
        
        for i in range(5):
            res = requests.get(f"{BASE_URL}/task/{task_id}", timeout=10)
            data = res.json()
            print(f"Poll {i+1}: Status = {data.get('status')}")
            
            if data.get('status') == 'completed':
                print("✓ TASK COMPLETED")
                if 'questions' in data:
                    print(f"  -> Generated {len(data['questions'])} questions")
                break
            elif data.get('status') == 'failed':
                print("✗ TASK FAILED")
                print(f"  Error: {data.get('error')}")
                break
            
            if i < 4:
                import time
                time.sleep(2)
    else:
        print(f"✗ Generate failed: {res.status_code}")
        
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {str(e)}")

print("\n" + "="*70)
