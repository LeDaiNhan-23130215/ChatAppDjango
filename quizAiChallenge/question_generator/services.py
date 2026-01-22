import logging
from quiz.models import Question

logger = logging.getLogger(__name__)

def save_questions_to_db(questions: list):
    """
    Nhận list câu hỏi JSON từ AI worker và lưu vào database
    
    Args:
        questions: List of question dictionaries from AI worker
    
    Returns:
        Number of questions saved
        
    Raises:
        KeyError: If required fields are missing
        Exception: If database operation fails
    """
    if not questions:
        logger.warning("save_questions_to_db called with empty questions list")
        return 0
    
    objs = []
    
    try:
        for idx, q in enumerate(questions):
            try:
                # Validate required fields
                if "sentence" not in q:
                    raise KeyError(f"Question {idx}: 'sentence' field is required")
                if "options" not in q or not all(k in q["options"] for k in ["A", "B", "C", "D"]):
                    raise KeyError(f"Question {idx}: 'options' must contain A, B, C, D")
                if "correct_answer" not in q:
                    raise KeyError(f"Question {idx}: 'correct_answer' field is required")
                
                obj = Question(
                    text=q["sentence"],
                    directive=q.get("directive", ""),
                    a=q["options"]["A"],
                    b=q["options"]["B"],
                    c=q["options"]["C"],
                    d=q["options"]["D"],
                    correct=q["correct_answer"],
                    explanation=q.get("explanation"),
                    question_type=q.get("type"),
                    difficulty=q.get("difficulty"),
                    score=q.get("score", 0),
                    context=q.get("context"),
                )
                objs.append(obj)
            except KeyError as e:
                logger.error(f"Error processing question {idx}: {str(e)}")
                raise
        
        # Bulk create all objects
        created = Question.objects.bulk_create(objs)
        logger.info(f"Successfully created {len(created)} questions")
        return len(created)
        
    except Exception as e:
        logger.error(f"Error in save_questions_to_db: {str(e)}")
        raise
