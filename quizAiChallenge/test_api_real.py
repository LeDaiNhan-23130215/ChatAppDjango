#!/usr/bin/env python
"""
Script test API thực tế với ngrok
"""
import requests
import json
import time

# API URL
API_BASE = "http://127.0.0.1:8000"
AI_TOKEN = "38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21"

def test_request_ai_questions():
    """Test gửi request tới AI worker"""
    print("\n" + "="*60)
    print("TEST 1: Gửi request tới AI worker")
    print("="*60)
    
    payload = {
        "user_id": "test_user_001",
        "quiz_size": 5,
        "declared_level": "Intermediate",
        "profession": "engineer",
        "preferred_topics": ["English", "Grammar"],
        "weak_skills": ["Listening"]
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/ai/generate/",
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 202 or response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_receive_ai_questions():
    """Test nhận câu hỏi từ AI worker"""
    print("\n" + "="*60)
    print("TEST 2: Nhận câu hỏi từ AI worker")
    print("="*60)
    
    questions = [
        {
            "sentence": "What is the capital of France?",
            "directive": "Choose the correct answer",
            "options": {
                "A": "London",
                "B": "Paris",
                "C": "Berlin",
                "D": "Rome"
            },
            "correct_answer": "B",
            "explanation": "Paris is the capital of France",
            "type": "multiple_choice",
            "difficulty": "easy",
            "score": 10,
            "context": "geography"
        },
        {
            "sentence": "What is 2 + 2?",
            "directive": "",
            "options": {
                "A": "3",
                "B": "4",
                "C": "5",
                "D": "6"
            },
            "correct_answer": "B",
            "explanation": "2+2=4",
            "type": "multiple_choice",
            "difficulty": "easy",
            "score": 5,
            "context": "math"
        }
    ]
    
    payload = {
        "questions": questions,
        "user_id": "test_user_001"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/ai/receive/",
            json=payload,
            headers={"X-AI-Worker-Token": AI_TOKEN},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_invalid_json():
    """Test gửi JSON không hợp lệ"""
    print("\n" + "="*60)
    print("TEST 3: Test với JSON không hợp lệ")
    print("="*60)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/ai/generate/",
            data="invalid json",
            content_type='application/json',
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_missing_fields():
    """Test gửi dữ liệu thiếu field bắt buộc"""
    print("\n" + "="*60)
    print("TEST 4: Test với dữ liệu thiếu user_id")
    print("="*60)
    
    payload = {
        "quiz_size": 10
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/ai/generate/",
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_unauthorized():
    """Test gửi request không có token"""
    print("\n" + "="*60)
    print("TEST 5: Test unauthorized (không có token)")
    print("="*60)
    
    payload = {
        "questions": [{
            "sentence": "Test",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "A"
        }],
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/ai/receive/",
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 401
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_wrong_token():
    """Test gửi request với token sai"""
    print("\n" + "="*60)
    print("TEST 6: Test với token sai")
    print("="*60)
    
    payload = {
        "questions": [{
            "sentence": "Test",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "A"
        }],
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/ai/receive/",
            json=payload,
            headers={"X-AI-Worker-Token": "wrong_token"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 401
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "🧪 BẮT ĐẦU TEST API QUESTION_GENERATOR " + "="*30)
    
    results = {}
    results["Test 1: Request AI questions"] = test_request_ai_questions()
    results["Test 2: Receive AI questions"] = test_receive_ai_questions()
    results["Test 3: Invalid JSON"] = test_invalid_json()
    results["Test 4: Missing fields"] = test_missing_fields()
    results["Test 5: Unauthorized (no token)"] = test_unauthorized()
    results["Test 6: Wrong token"] = test_wrong_token()
    
    print("\n" + "="*60)
    print("KẾT QUẢ TỔNG HỢPKẾT QUẢ TỔNG HỢP")
    print("="*60)
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTổng: {passed}/{len(results)} tests passed")
    if passed == len(results):
        print("\n🎉 TẤT CẢ TESTS ĐÃ PASS!")
    else:
        print(f"\n⚠️ Còn {len(results) - passed} tests failed")
