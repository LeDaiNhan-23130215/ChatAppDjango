"""
Test chính xác như Colab của bạn
"""
import requests
import json

url = "https://nonelliptic-dewily-carlos.ngrok-free.dev/generate"

payload = {
    "user_id": 1,
    "quiz_size": 3,
    "declared_level": "Advanced",
    "profession": "engineer",
    "weak_skills": ["grammar"],
    "preferred_topics": ["APIs", "databases"],
    "sync": True   # Quan trong nhat
}

print("="*70)
print("TEST TAO CAU HOI (Exact Colab)")
print("="*70)
print(f"\nURL: {url}")
print(f"\nPayload:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

print("\nDang gui request (timeout 300 giay)...")
print("-"*70)

try:
    res = requests.post(url, json=payload, timeout=300)
    print(f"\nStatus: {res.status_code}")
    print(f"Response:")
    
    if res.text:
        data = res.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Check so cau hoi
        if isinstance(data, dict) and "questions" in data:
            print(f"\n==> TAO THANH CONG {len(data['questions'])} CAU HOI!")
            for i, q in enumerate(data['questions'], 1):
                print(f"\n[Cau {i}] {q.get('sentence', 'N/A')[:60]}...")
    else:
        print("(No response text)")
        
except requests.Timeout:
    print("TIMEOUT: Khong nhan response trong 300 giay")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*70)
