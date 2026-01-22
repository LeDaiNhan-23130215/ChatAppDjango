"""
Test tạo câu hỏi từ AI worker và polling kết quả
"""
import requests
import json
import time

# AI Worker endpoints (ngrok)
generate_url = "https://nonelliptic-dewily-carlos.ngrok-free.dev/generate"
result_url = "https://nonelliptic-dewily-carlos.ngrok-free.dev/result"

print("="*70)
print("🚀 TEST TẠO CÂU HỎI TỪ AI WORKER (NGROK) - With Polling")
print("="*70)

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

print(f"\n📤 Gửi request tới: {generate_url}")
print(f"\n📋 Payload:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

print("\n⏳ Đang chờ response từ AI worker (timeout 300 giây)...")
print("-" * 70)

try:
    start_time = time.time()
    res = requests.post(generate_url, json=payload, timeout=300)
    elapsed = time.time() - start_time
    
    print(f"\n✓ Nhận response sau {elapsed:.1f} giây")
    print(f"Status Code: {res.status_code}")
    print("-" * 70)
    
    if res.text:
        data = res.json()
        print("\n📥 Response từ AI Worker:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Kiểm tra xem có questions trực tiếp không
        if "questions" in data:
            print("\n✅ Nhận câu hỏi trực tiếp!")
            num_questions = len(data["questions"])
            print(f"   Tạo thành công {num_questions} câu hỏi!")
            
            # In chi tiết từng câu hỏi
            print_questions(data["questions"])
        
        # Hoặc có task_id cần poll
        elif "task_id" in data and data.get("status") == "accepted":
            task_id = data["task_id"]
            print(f"\n⏳ Task accepted. Task ID: {task_id}")
            print(f"   Polling kết quả...")
            
            # Polling loop
            max_polls = 60  # Max 60 lần poll
            poll_count = 0
            
            while poll_count < max_polls:
                poll_count += 1
                time.sleep(2)  # Chờ 2 giây trước poll tiếp
                
                try:
                    result_res = requests.get(
                        f"{result_url}/{task_id}",
                        timeout=10
                    )
                    
                    if result_res.status_code == 200:
                        result_data = result_res.json()
                        
                        if result_data.get("status") == "completed":
                            print(f"\n✅ Task completed sau {poll_count * 2} giây!")
                            
                            if "questions" in result_data:
                                print_questions(result_data["questions"])
                            elif "result" in result_data and "questions" in result_data["result"]:
                                print_questions(result_data["result"]["questions"])
                            else:
                                print("\nResult data:")
                                print(json.dumps(result_data, indent=2, ensure_ascii=False))
                            break
                        
                        elif result_data.get("status") == "pending":
                            print(f"   Poll {poll_count}: Still processing...")
                        else:
                            print(f"   Status: {result_data.get('status')}")
                            if "error" in result_data:
                                print(f"   Error: {result_data['error']}")
                                break
                    
                except Exception as e:
                    print(f"   Poll {poll_count} error: {str(e)}")
            
            if poll_count >= max_polls:
                print(f"\n⚠️  Timeout: Không nhận kết quả sau {max_polls * 2} giây")
        
        else:
            print("\n⚠️  Không tìm thấy questions hoặc task_id")
            print("Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

except requests.Timeout:
    print(f"\n✗ TIMEOUT: AI worker không phản hồi trong 300 giây")
except requests.ConnectionError as e:
    print(f"\n✗ CONNECTION ERROR: {str(e)}")
    print("  Kiểm tra:")
    print("  - Ngrok có đang chạy không?")
    print("  - URL ngrok còn hiệu lực không?")
except requests.RequestException as e:
    print(f"\n✗ REQUEST ERROR: {str(e)}")
except json.JSONDecodeError:
    print("\n✗ ERROR: Response không phải JSON")
    if 'res' in locals() and hasattr(res, 'text'):
        print(f"Response text: {res.text[:500]}")
except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")

print("\n" + "="*70)

def print_questions(questions):
    """In chi tiết từng câu hỏi"""
    print("\n" + "="*70)
    print("📝 CHI TIẾT CÂU HỎI:")
    print("="*70)
    
    for i, q in enumerate(questions, 1):
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
