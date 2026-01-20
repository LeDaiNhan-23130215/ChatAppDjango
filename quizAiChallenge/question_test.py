import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')
django.setup()

from quiz.models import Question

# Xóa câu hỏi cũ
Question.objects.all().delete()

questions_data = [
    {
        "text": "The project manager _____ the team about the deadline changes yesterday.",
        "directive": "Choose the best word/phrase to complete the sentence:",
        "a": "informed",
        "b": "informs",
        "c": "has informed",
        "d": "is informing",
        "correct": "A",
        "explanation": "Past tense 'informed' is correct because the action happened 'yesterday'. The other options use present tense or present perfect, which don't match the past time reference.",
        "question_type": "grammar",
        "difficulty": "intermediate",
        "score": 5,
        "context": "Business communication"
    },
    {
        "text": "Despite _____ challenges during the agile sprint, the team delivered the features on time.",
        "directive": "Choose the best word/phrase to complete the sentence:",
        "a": "facing",
        "b": "to face",
        "c": "the face",
        "d": "faced",
        "correct": "A",
        "explanation": "'Facing' is a gerund that follows the preposition 'despite'. The other options are either infinitive forms or incorrect verb forms that don't work after prepositions.",
        "question_type": "grammar",
        "difficulty": "advanced",
        "score": 7,
        "context": "Agile meetings"
    },
    {
        "text": "The code _____ bugs because the developer didn't test it thoroughly.",
        "directive": "Choose the best word/phrase to complete the sentence:",
        "a": "contains",
        "b": "contain",
        "c": "is containing",
        "d": "contained",
        "correct": "A",
        "explanation": "'Contains' (present simple) is appropriate here as it describes a current state or general fact. The singular subject 'code' requires the singular verb form.",
        "question_type": "grammar",
        "difficulty": "intermediate",
        "score": 6,
        "context": "Coding/debugging"
    },
    {
        "text": "Which word means to find and remove errors from a program?",
        "directive": "Select the correct vocabulary word:",
        "a": "compile",
        "b": "debug",
        "c": "execute",
        "d": "deploy",
        "correct": "B",
        "explanation": "'Debug' means to identify and fix errors in code. 'Compile' is converting code to machine language, 'execute' is running code, and 'deploy' is releasing software to production.",
        "question_type": "vocabulary",
        "difficulty": "intermediate",
        "score": 6,
        "context": "Coding/debugging"
    },
    {
        "text": "In agile methodology, a _____ is a regular meeting where the team discusses progress and obstacles.",
        "directive": "Choose the best word/phrase to complete the sentence:",
        "a": "retrospective",
        "b": "standstill",
        "c": "standup",
        "d": "shutdown",
        "correct": "C",
        "explanation": "A 'standup' (or daily standup) is a short daily meeting in agile where team members share updates. 'Retrospective' is for reviewing completed sprints, and the others are not relevant.",
        "question_type": "vocabulary",
        "difficulty": "advanced",
        "score": 8,
        "context": "Agile meetings"
    },
    {
        "text": "The project _____. It _____.",
        "directive": "Choose the options that best complete both sentences:",
        "a": "is delayed / will be completed next month",
        "b": "was delayed / is being completed next month",
        "c": "is being delayed / will complete next month",
        "d": "was being delayed / is completed next month",
        "correct": "A",
        "explanation": "Present tense 'is delayed' describes the current situation, and future ense 'will be completed' describes future plans. Option B uses 'is being completed' which implies active ongoing work, not a scheduled future event.",
        "question_type": "grammar",
        "difficulty": "advanced",
        "score": 9,
        "context": "Project management"
    },
    {
        "text": "The debugging process requires _____ and systematic testing to identify all potential issues.",
        "directive": "Choose the best word/phrase to complete the sentence:",
        "a": "patience",
        "b": "patient",
        "c": "patiently",
        "d": "impatience",
        "correct": "A",
        "explanation": "A noun is needed here to follow the verb 'requires'. 'Patience' is the correct noun form. 'Patient' is an adjective, 'patiently' is an adverb, and 'impatience' has the opposite meaning.",
        "question_type": "vocabulary",
        "difficulty": "intermediate",
        "score": 5,
        "context": "Coding/debugging"
    },
    {
        "text": "If the team _____ more time for testing, they _____ fewer bugs in production.",
        "directive": "Choose the best option for both blanks:",
        "a": "had / would have had",
        "b": "have had / would have",
        "c": "has / would have",
        "d": "had had / would have",
        "correct": "A",
        "explanation": "This is a conditional sentence (if clause + main clause). 'Had' (past perfect) in the if-clause and 'would have had' (conditional perfect) in the main clause express a hypothetical past situation.",
        "question_type": "grammar",
        "difficulty": "advanced",
        "score": 10,
        "context": "Software development"
    },
    {
        "text": "The framework _____ for building scalable web applications.",
        "directive": "Choose the best word/phrase to complete the sentence:",
        "a": "is used widely",
        "b": "is widely using",
        "c": "is widely used",
        "d": "widely uses",
        "correct": "C",
        "explanation": "'Is widely used' (passive voice with adverb placement) correctly shows that the framework is used by people. The adverb 'widely' modifies the past participle 'used'.",
        "question_type": "grammar",
        "difficulty": "intermediate",
        "score": 6,
        "context": "Coding/Web development"
    },
    {
        "text": "In scrum methodology, what is the term for a two-week iteration of work?",
        "directive": "Select the correct term:",
        "a": "Epic",
        "b": "User story",
        "c": "Sprint",
        "d": "Backlog",
        "correct": "C",
        "explanation": "'Sprint' is a fixed time period (usually 2 weeks) in scrum. 'Epic' is a large feature, 'user story' is a small requirement, and 'backlog' is a list of work items.",
        "question_type": "vocabulary",
        "difficulty": "intermediate",
        "score": 7,
        "context": "Agile meetings"
    },
]

# Thêm câu hỏi vào database
for q in questions_data:
    question = Question.objects.create(**q)
    print(f"✅ Added Question {question.id}: {q['text'][:50]}... (Score: {q['score']})")

print(f"\n📊 Total questions: {Question.objects.count()}")
