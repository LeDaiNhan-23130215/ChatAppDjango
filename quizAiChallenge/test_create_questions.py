"""
Test tạo câu hỏi từ AI worker
Chờ response từ AI (có thể chậm)
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_create_questions():
    """Test tạo câu hỏi từ AI worker"""
    
    print("\n" + "="*70)
    print("🧪 TEST TẠO CÂU HỎI TỪ AI WORKER")
    print("="*70)
    
    # Kiểm tra kết nối server
    print("\n1️⃣  Kiểm tra kết nối server...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✓ Server sẵn sàng (Status: {response.status_code})")
    except Exception as e:
        print(f"✗ Không thể kết nối: {str(e)}")
        return False
    
    # Request tạo câu hỏi
    print("\n2️⃣  Gửi request tạo câu hỏi...")
    payload = {
        "user_id": "test_user_" + str(int(time.time())),
        "quiz_size": 5,
        "declared_level": "Intermediate",
        "profession": "developer",
        "preferred_topics": ["Python", "Django"],
        "weak_skills": ["async", "websockets"]
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        print("\n⏳ Chờ response từ AI worker (có thể chậm, vui lòng đợi)...")
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate/",
            json=payload,
            timeout=120  # Chờ 2 phút
        )
        elapsed = time.time() - start_time
        
        print(f"\n✓ Nhận response sau {elapsed:.1f} giây")
        print(f"Status Code: {response.status_code}")
        
        if response.text:
            data = response.json()
            print(f"\nResponse từ AI Worker:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if response.status_code in [200, 202]:
                print("\n✅ REQUEST THÀNH CÔNG!")
                return True
            else:
                print(f"\n⚠️  Status code {response.status_code}")
        else:
            print("No response text")
            
    except requests.Timeout:
        print(f"✗ Timeout: AI worker không phản hồi trong 120 giây")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    return False

def test_receive_generated_questions():
    """Test nhận câu hỏi đã tạo từ AI"""
    
    print("\n" + "="*70)
    print("🧪 TEST NHẬN CÂU HỎI TỪ AI WORKER")
    print("="*70)
    
    # Mô phỏng câu hỏi từ AI
    questions = [
        {
            "sentence": "What is the difference between @app.route() and @app.get() in Flask?",
            "directive": "Choose the most accurate answer",
            "options": {
                "A": "@app.get() is only for HTTP GET requests, @app.route() supports all methods",
                "B": "They are identical, just different naming conventions",
                "C": "@app.route() is deprecated in new Flask versions",
                "D": "@app.get() is specifically for retrieving data from database"
            },
            "correct_answer": "A",
            "explanation": "@app.route() is a generic decorator that can handle multiple HTTP methods via the 'methods' parameter, while @app.get() is a shorthand that specifically registers a GET endpoint.",
            "type": "multiple_choice",
            "difficulty": "medium",
            "score": 15,
            "context": "Flask Web Framework"
        },
        {
            "sentence": "Which of these is NOT a feature of Django ORM?",
            "directive": "Select the incorrect statement",
            "options": {
                "A": "Lazy evaluation of querysets",
                "B": "Automatic SQL query optimization",
                "C": "Cross-database compatibility",
                "D": "Query chaining with method calls"
            },
            "correct_answer": "B",
            "explanation": "While Django ORM is powerful, it does not automatically optimize SQL queries. Developers need to use select_related(), prefetch_related() and other optimization techniques.",
            "type": "multiple_choice",
            "difficulty": "hard",
            "score": 20,
            "context": "Django Framework"
        },
        {
            "sentence": "What is async/await in Python used for?",
            "directive": "Choose the best explanation",
            "options": {
                "A": "Faster code execution",
                "B": "Writing concurrent code that is easier to read than callbacks",
                "C": "Automatically parallelizing code across multiple processors",
                "D": "Replacing all threading functionality"
            },
            "correct_answer": "B",
            "explanation": "async/await provides a way to write asynchronous code with a synchronous-like syntax, making it more readable than traditional callback-based async code.",
            "type": "multiple_choice",
            "difficulty": "medium",
            "score": 15,
            "context": "Python Async"
        }
    ]
    
    AI_TOKEN = "38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21"
    
    print(f"\n1️⃣  Gửi {len(questions)} câu hỏi tới Django...")
    
    payload = {
        "questions": questions,
        "user_id": "test_user_" + str(int(time.time()))
    }
    
    headers = {
        "X-AI-Worker-Token": AI_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/receive/",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.text:
            data = response.json()
            print(f"\nResponse:")
            print(json.dumps(data, indent=2))
            
            if response.status_code == 201:
                print(f"\n✅ ĐÃ LƯU {data.get('saved', 0)} CÂU HỎI VÀO DATABASE!")
                return True
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("\n🚀 BẮT ĐẦU TEST CHỨC NĂNG TẠO CÂU HỎI\n")
    
    # Test 1: Request tạo câu hỏi
    result1 = test_create_questions()
    
    time.sleep(2)
    
    # Test 2: Receive/save câu hỏi
    result2 = test_receive_generated_questions()
    
    print("\n" + "="*70)
    if result1 and result2:
        print("✅ TẤT CẢ TESTS PASSED!")
    else:
        print("⚠️  Một số tests không passed")
        if not result1:
            print("  - Request tạo câu hỏi thất bại")
        if not result2:
            print("  - Nhận/lưu câu hỏi thất bại")
    print("="*70 + "\n")
