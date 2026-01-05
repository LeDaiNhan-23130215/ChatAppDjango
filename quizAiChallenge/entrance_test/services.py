from .models import Choice, EntranceTestResult, UserAnswer, Question
from collections import defaultdict

PART_LEARNING_CONTENT = {
    1: [
        'Nhận diện hành động & bối cảnh trong hình ảnh',
        'Từ vựng mô tả người, vật, địa điểm',
    ],
    2: [
        'Mẫu câu hỏi thường gặp trong Part 2',
        'Bẫy từ đồng âm và từ phủ định',
    ],
    3: [
        'Nghe ý chính trong hội thoại ngắn',
        'Xác định người nói, địa điểm, mục đích',
    ],
    4: [
        'Nghe thông báo và bài nói ngắn',
        'Tập trung từ khóa và ngữ cảnh',
    ],
    5: [
        'Ngữ pháp trọng tâm TOEIC',
        'Từ loại và cấu trúc câu',
    ],
    6: [
        'Hoàn thành đoạn văn',
        'Liên kết câu và ngữ pháp trong ngữ cảnh',
    ],
    7: [
        'Đọc hiểu email, thông báo',
        'Chiến thuật skimming & scanning',
    ],
}

LEVEL_ADJUSTMENT = {
    'beginner': [
        'Học lại kiến thức nền tảng',
        'Làm bài tập dễ trước',
    ],
    'intermediate': [
        'Luyện tập mức trung bình',
        'Tăng tốc độ làm bài',
    ],
    'advanced': [
        'Làm đề nâng cao',
        'Chiến thuật đạt điểm cao',
    ],
}

def cal_result(user, test, user_answers):
    correct = 0
    total = len(user_answers)
    result = EntranceTestResult.objects.create(
        user = user,
        test = test,
        score = 0,
        correct_answers = 0,
        total_questions = total,
        level = 'beginner',
    )
    for question_id, choice_id in user_answers.items():
        choice = Choice.objects.get(id = choice_id)
        
        UserAnswer.objects.create(
            result = result,
            question_id = question_id,
            selected_choice = choice
        )

        if choice.is_correct:
            correct += 1
    
    score = int((correct / total) * 100)
    level = map_score_to_level(score)
    result.score = score
    result.correct_answers = correct
    result.level = level
    result.save()

    return result

def map_score_to_level(score):
    if score < 40:
        return 'BEGINNER'
    elif score < 70:
        return 'INTERMEDIATE'
    return 'ADVANCED'

def analyze_weak_parts(result):
    part_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

    answers = UserAnswer.objects.select_related(
        'question'
    ).filter(result = result)

    for ans in answers:
        part = ans.question.part
        part_stats[part]['total'] += 1

        if ans.is_correct():
            part_stats[part]['correct'] += 1
    
    weak_parts = []
    ALL_PARTS = [1,2,3,4,5,6,7]
    for part in ALL_PARTS:
        stats = part_stats.get(part, {'correct': 0, 'total': 0})

        if stats['total'] == 0:
            accuracy = 0
        else:
            accuracy =  stats['correct'] / stats['total']

            if accuracy < 0.6:
                weak_parts.append(dict(
                    part = part,
                    accuracy = round(accuracy * 100)
                ))
    
    return weak_parts

def get_part_display(part_number):
    return dict(Question.PART_CHOICES).get(part_number)