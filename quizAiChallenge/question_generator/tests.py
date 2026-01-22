from django.test import TestCase, Client
from django.urls import reverse
from django.test import override_settings
from quiz.models import Question
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import json

User = get_user_model()

@override_settings(
    AI_WORKER_TOKEN="38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21",
    AI_WORKER_URL="https://nonelliptic-dewily-carlos.ngrok-free.dev"
)
class QuestionGeneratorTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.ai_token = "38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21"
        
    def test_request_ai_questions_post_only(self):
        """Test that GET requests are rejected"""
        response = self.client.get('/api/ai/generate/')
        self.assertEqual(response.status_code, 405)
        
    def test_request_ai_questions_missing_user_id(self):
        """Test that missing user_id returns 400"""
        response = self.client.post(
            '/api/ai/generate/',
            data=json.dumps({"quiz_size": 10}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("user_id", data["error"])
        
    def test_request_ai_questions_invalid_json(self):
        """Test that invalid JSON returns 400"""
        response = self.client.post(
            '/api/ai/generate/',
            data="invalid json",
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
    @patch('question_generator.views.requests.post')
    def test_request_ai_questions_success(self, mock_post):
        """Test successful request to AI worker"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "pending", "task_id": "12345"}
        mock_response.status_code = 202
        mock_post.return_value = mock_response
        
        payload = {
            "user_id": "user123",
            "quiz_size": 20,
            "declared_level": "Advanced",
            "profession": "engineer"
        }
        
        response = self.client.post(
            '/api/ai/generate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 202)
        data = json.loads(response.content)
        self.assertEqual(data["task_id"], "12345")
        
    @patch('question_generator.views.requests.post')
    def test_request_ai_questions_worker_unavailable(self, mock_post):
        """Test handling when AI worker is unavailable"""
        mock_post.side_effect = Exception("Connection refused")
        
        payload = {
            "user_id": "user123",
            "quiz_size": 20
        }
        
        response = self.client.post(
            '/api/ai/generate/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 503)
        

@override_settings(
    AI_WORKER_TOKEN="38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21",
    AI_WORKER_URL="https://nonelliptic-dewily-carlos.ngrok-free.dev"
)
class ReceiveQuestionsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.ai_token = "38bnDJIXRQfPlA0mgCWUksNRPRV_49ott2Dud69FqNoVeq21"
        self.valid_questions = [
            {
                "sentence": "What is 2+2?",
                "directive": "Choose the correct answer",
                "options": {
                    "A": "3",
                    "B": "4",
                    "C": "5",
                    "D": "6"
                },
                "correct_answer": "B",
                "explanation": "2+2 equals 4",
                "type": "multiple_choice",
                "difficulty": "easy",
                "score": 10,
                "context": "math"
            },
            {
                "sentence": "What is the capital of France?",
                "directive": "",
                "options": {
                    "A": "London",
                    "B": "Berlin",
                    "C": "Paris",
                    "D": "Rome"
                },
                "correct_answer": "C",
                "explanation": "Paris is the capital of France",
                "type": "multiple_choice",
                "difficulty": "easy",
                "score": 5,
                "context": "geography"
            }
        ]
        
    def test_receive_questions_post_only(self):
        """Test that GET requests are rejected"""
        response = self.client.get('/api/ai/receive/')
        self.assertEqual(response.status_code, 405)
        
    def test_receive_questions_unauthorized_no_token(self):
        """Test that missing token returns 401"""
        response = self.client.post(
            '/api/ai/receive/',
            data=json.dumps({"questions": self.valid_questions}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        
    def test_receive_questions_unauthorized_wrong_token(self):
        """Test that wrong token returns 401"""
        response = self.client.post(
            '/api/ai/receive/',
            data=json.dumps({"questions": self.valid_questions}),
            content_type='application/json',
            HTTP_X_AI_WORKER_TOKEN="wrong_token"
        )
        self.assertEqual(response.status_code, 401)
        
    def test_receive_questions_invalid_json(self):
        """Test that invalid JSON returns 400"""
        response = self.client.post(
            '/api/ai/receive/',
            data="invalid json",
            content_type='application/json',
            HTTP_X_AI_WORKER_TOKEN=self.ai_token
        )
        self.assertEqual(response.status_code, 400)
        
    def test_receive_questions_empty_list(self):
        """Test that empty questions list returns 400"""
        response = self.client.post(
            '/api/ai/receive/',
            data=json.dumps({"questions": []}),
            content_type='application/json',
            HTTP_X_AI_WORKER_TOKEN=self.ai_token
        )
        self.assertEqual(response.status_code, 400)
        
    def test_receive_questions_missing_required_field(self):
        """Test that missing required fields returns 500"""
        invalid_questions = [
            {
                "directive": "Choose",
                # Missing 'sentence'
                "options": {
                    "A": "1",
                    "B": "2",
                    "C": "3",
                    "D": "4"
                },
                "correct_answer": "A"
            }
        ]
        
        response = self.client.post(
            '/api/ai/receive/',
            data=json.dumps({"questions": invalid_questions, "user_id": "user123"}),
            content_type='application/json',
            HTTP_X_AI_WORKER_TOKEN=self.ai_token
        )
        self.assertEqual(response.status_code, 500)
        
    def test_receive_questions_success(self):
        """Test successfully receiving and saving questions"""
        initial_count = Question.objects.count()
        
        response = self.client.post(
            '/api/ai/receive/',
            data=json.dumps({
                "questions": self.valid_questions,
                "user_id": "user123"
            }),
            content_type='application/json',
            HTTP_X_AI_WORKER_TOKEN=self.ai_token
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["saved"], 2)
        
        # Verify questions were saved
        self.assertEqual(Question.objects.count(), initial_count + 2)
        
        # Verify first question
        q1 = Question.objects.first()
        self.assertEqual(q1.text, "What is 2+2?")
        self.assertEqual(q1.correct, "B")
        self.assertEqual(q1.a, "3")
        self.assertEqual(q1.d, "6")
        
    def test_receive_questions_bulk_save(self):
        """Test that questions are bulk created correctly"""
        initial_count = Question.objects.count()
        
        # Create multiple questions
        questions = [self.valid_questions[0]] * 5
        
        response = self.client.post(
            '/api/ai/receive/',
            data=json.dumps({
                "questions": questions,
                "user_id": "user456"
            }),
            content_type='application/json',
            HTTP_X_AI_WORKER_TOKEN=self.ai_token
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["saved"], 5)
        self.assertEqual(Question.objects.count(), initial_count + 5)
