"""
Test tạo câu hỏi - thử không dùng sync hoặc dùng cách khác
"""
import requests
import json

print("="*70)
print("TEST 1: Khong dung sync")
print("="*70)

url = "https://nonelliptic-dewily-carlos.ngrok-free.dev/generate"
payload = {
    "user_id": 1,
    "quiz_size": 3,
    "declared_level": "Advanced",
    "profession": "engineer",
    "weak_skills": ["grammar"],
    "preferred_topics": ["APIs", "databases"]
}

print(f"\nURL: {url}")
print(f"Payload (khong sync):")
print(json.dumps(payload, indent=2, ensure_ascii=False))

try:
    res = requests.post(url, json=payload, timeout=300)
    print(f"\nStatus: {res.status_code}")
    print(f"Response:")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70)
print("TEST 2: Voi sync=False")
print("="*70)

payload2 = {
    "user_id": 2,
    "quiz_size": 3,
    "declared_level": "Advanced",
    "profession": "engineer",
    "weak_skills": ["grammar"],
    "preferred_topics": ["APIs", "databases"],
    "sync": False
}

print(f"\nPayload (sync=False):")
print(json.dumps(payload2, indent=2, ensure_ascii=False))

try:
    res2 = requests.post(url, json=payload2, timeout=300)
    print(f"\nStatus: {res2.status_code}")
    print(f"Response:")
    print(json.dumps(res2.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70)
print("TEST 3: Thu endpoints khac")
print("="*70)

# List endpoints
endpoints = [
    "https://nonelliptic-dewily-carlos.ngrok-free.dev/",
    "https://nonelliptic-dewily-carlos.ngrok-free.dev/api",
    "https://nonelliptic-dewily-carlos.ngrok-free.dev/status"
]

for endpoint in endpoints:
    try:
        r = requests.get(endpoint, timeout=5)
        print(f"\nOK: {endpoint}")
        print(f"  Status: {r.status_code}")
        if r.text and len(r.text) < 200:
            print(f"  Response: {r.text}")
    except Exception as e:
        print(f"\nFAIL: {endpoint}: {str(e)[:50]}")
