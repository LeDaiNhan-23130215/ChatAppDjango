import logging
from quiz.models import Question

logger = logging.getLogger(__name__)

def save_questions_to_db(questions, user_id=None):
    print("DEBUG: Bắt đầu save_questions_to_db")
    print(f"DEBUG: Số lượng questions nhận được: {len(questions)}")
    print("DEBUG: Questions data mẫu:", questions[0] if questions else "Empty list")

    try:
        from quiz.models import Question  # import ở đây để tránh circular import nếu có
        created_count = 0

        for q_data in questions:
            print("DEBUG: Đang lưu câu hỏi:", q_data.get('sentence', 'N/A'))
            print("DEBUG: Options:", q_data.get('options', {}))
            print("DEBUG: Correct:", q_data.get('correct_answer'))

            # Mapping field (điều chỉnh theo model thực tế của bạn)
            Question.objects.create(
                text=q_data.get('sentence') or q_data.get('directive', ''),
                a=q_data['options'].get('A', ''),
                b=q_data['options'].get('B', ''),
                c=q_data['options'].get('C', ''),
                d=q_data['options'].get('D', ''),
                correct=q_data.get('correct_answer', ''),
                explanation=q_data.get('explanation', ''),
                question_type=q_data.get('type', ''),
                difficulty=q_data.get('difficulty', ''),
                score=q_data.get('score'),
                context=q_data.get('context', ''),
                category=q_data.get('category', ''),  # nếu có
            )
            created_count += 1

        print(f"DEBUG: Đã tạo thành công {created_count} câu hỏi")
        return created_count

    except Exception as e:
        print("DEBUG: LỖI khi lưu DB:", str(e))
        print("DEBUG: Traceback:", e.__traceback__)
        raise  # raise lại để view catch và log