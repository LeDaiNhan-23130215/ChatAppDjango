"""
Test AI Worker với endpoint /health, /generate, /task/<task_id>
"""
import requests
import json
import time

BASE_URL = "https://nonelliptic-dewily-carlos.ngrok-free.dev"

print("="*70)
print("TEST AI WORKER ENDPOINTS")
print("="*70)

# Step 1: Check health
print("\n[1] Checking health...")
try:
    res = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}")
    if res.status_code != 200:
        print("ERROR: Health check failed!")
        exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# Step 2: Generate questions
print("\n[2] Sending generate request...")
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
        timeout=10
    )
    print(f"\nStatus: {res.status_code}")
    data = res.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if res.status_code != 202:
        print(f"ERROR: Expected 202, got {res.status_code}")
        exit(1)
    
    task_id = data.get("task_id")
    if not task_id:
        print("ERROR: No task_id in response")
        exit(1)
        
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# Step 3: Poll for task result
print(f"\n[3] Polling task {task_id}...")

max_polls = 120  # 4 minutes max
poll_interval = 2  # 2 seconds

for poll_count in range(max_polls):
    try:
        res = requests.get(
            f"{BASE_URL}/task/{task_id}",
            timeout=10
        )
        
        if res.status_code != 200:
            print(f"Poll {poll_count}: Status {res.status_code}")
            time.sleep(poll_interval)
            continue
        
        data = res.json()
        status = data.get("status")
        
        print(f"Poll {poll_count}: {status}")
        
        if status == "completed":
            print(f"\nTASK COMPLETED!")
            print(f"\nFull Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check for questions
            if "questions" in data:
                questions = data["questions"]
                print(f"\n{'='*70}")
                print(f"SUCCESS: Generated {len(questions)} questions!")
                print(f"{'='*70}")
                
                for i, q in enumerate(questions, 1):
                    print(f"\n[Question {i}]")
                    print(f"  Text: {q.get('sentence', 'N/A')[:70]}...")
                    print(f"  Type: {q.get('type', 'N/A')}")
                    print(f"  Difficulty: {q.get('difficulty', 'N/A')}")
                    print(f"  Options:")
                    if "options" in q:
                        for key, val in q["options"].items():
                            mark = " <-- CORRECT" if q.get("correct_answer") == key else ""
                            print(f"    {key}: {val}{mark}")
                    if q.get("explanation"):
                        print(f"  Explanation: {q['explanation'][:100]}...")
            
            break
        
        elif status == "failed":
            print(f"TASK FAILED!")
            if "error" in data:
                print(f"Error: {data['error']}")
            break
        
        elif status in ["queued", "processing"]:
            print(f"  Still processing... waiting {poll_interval}s")
            time.sleep(poll_interval)
        
        else:
            print(f"  Unknown status: {status}")
            print(f"  Data: {json.dumps(data, indent=2)}")
            time.sleep(poll_interval)
    
    except requests.Timeout:
        print(f"Poll {poll_count}: Timeout")
        time.sleep(poll_interval)
    
    except Exception as e:
        print(f"Poll {poll_count}: Error - {e}")
        time.sleep(poll_interval)

if poll_count >= max_polls - 1:
    print(f"\nTIMEOUT: Task did not complete after {max_polls * poll_interval} seconds")

print("\n" + "="*70)
