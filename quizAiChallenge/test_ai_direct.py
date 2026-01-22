"""
Test tạo câu hỏi trực tiếp từ AI worker (ngrok)
Theo mẫu của Colab
"""
import requests
import json
import time

# AI Worker endpoint (ngrok)
url = "https://nonelliptic-dewily-carlos.ngrok-free.dev/generate"

# Payload để test
payload = {
    "user_id": 1,
    "quiz_size": 3,
    "declared_level": "Advanced",
    "profession": "engineer",
    "weak_skills": ["grammar"],
    "preferred_topics": ["APIs", "databases"],
    "sync": True   # ⚠️ rất quan trọng để test nhanh
}

print("="*70)
print("🚀 TEST TẠO CÂU HỎI TỪ AI WORKER (NGROK)")
print("="*70)
print(f"\n📤 Gửi request tới: {url}")
print(f"\n📋 Payload:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

print("\n⏳ Đang chờ response từ AI worker (timeout 300 giây)...")
print("-" * 70)

try:
    start_time = time.time()
    res = requests.post(url, json=payload, timeout=300)
    elapsed = time.time() - start_time
    
    print(f"\n✓ Nhận response sau {elapsed:.1f} giây\n")
    print(f"Status Code: {res.status_code}")
    print("-" * 70)
    
    if res.text:
        data = res.json()
        print("\n📥 Response từ AI Worker:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Kiểm tra số câu hỏi
        if "questions" in data:
            num_questions = len(data["questions"])
            print(f"\n✅ Tạo thành công {num_questions} câu hỏi!")
            
            # In chi tiết từng câu hỏi
            print("\n" + "="*70)
            print("📝 CHI TIẾT CÂU HỎI:")
            print("="*70)
            
            for i, q in enumerate(data["questions"], 1):
                print(f"\n📌 Câu hỏi {i}:")
                print(f"   Nội dung: {q.get('sentence', 'N/A')}")
                print(f"   Loại: {q.get('type', 'N/A')}")
                print(f"   Độ khó: {q.get('difficulty', 'N/A')}")
                print(f"   Điểm: {q.get('score', 'N/A')}")
                
                if "options" in q:
                    print(f"   Đáp án:")
                    for key, value in q["options"].items():
                        mark = " ✓" if q.get("correct_answer") == key else ""
                        print(f"     {key}: {value}{mark}")
                
                if q.get("explanation"):
                    print(f"   Giải thích: {q['explanation']}")
        else:
            print("\n⚠️  Không tìm thấy 'questions' trong response")
    else:
        print("No response text")

except requests.Timeout:
    print(f"✗ TIMEOUT: AI worker không phản hồi trong 300 giây")
except requests.ConnectionError as e:
    print(f"✗ CONNECTION ERROR: {str(e)}")
    print("  Kiểm tra:")
    print("  - Ngrok có đang chạy không?")
    print("  - URL ngrok còn hiệu lực không?")
except requests.RequestException as e:
    print(f"✗ REQUEST ERROR: {str(e)}")
except json.JSONDecodeError:
    print("✗ ERROR: Response không phải JSON")
    print(f"Response text: {res.text[:500]}")
except Exception as e:
    print(f"✗ ERROR: {str(e)}")

print("\n" + "="*70)
