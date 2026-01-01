from entrance_test.models import EntranceTest, Question, Choice


def run():
    # 1. Tạo hoặc lấy bài test
    test, created = EntranceTest.objects.get_or_create(
        title="TOEIC Entrance Test",
        defaults={
            "description": "TOEIC entrance test with passages for skill analysis",
            "is_active": True
        }
    )

    # 2. Xóa dữ liệu cũ
    test.questions.all().delete()

    questions_data = [

        # ================= PART 1 (2) =================
        {
            "part": 1,
            "passage": None,
            "content": "What can be seen in the picture?",
            "choices": [
                ("A man is answering the phone", False),
                ("A woman is typing on a laptop", True),
                ("People are having a meeting", False),
                ("The office is empty", False),
            ]
        },
        {
            "part": 1,
            "passage": None,
            "content": "What is the man doing?",
            "choices": [
                ("He is giving instructions", True),
                ("He is eating lunch", False),
                ("He is repairing a machine", False),
                ("He is answering emails", False),
            ]
        },

        # ================= PART 2 (2) =================
        {
            "part": 2,
            "passage": None,
            "content": "When will the meeting start?",
            "choices": [
                ("In the conference room", False),
                ("At 9 a.m.", True),
                ("With the manager", False),
                ("Yes, it has started", False),
            ]
        },
        {
            "part": 2,
            "passage": None,
            "content": "Where is the invoice?",
            "choices": [
                ("I sent it by email", True),
                ("Yesterday afternoon", False),
                ("With the accountant", False),
                ("At three o’clock", False),
            ]
        },

        # ================= PART 3 – Conversation 1 (2) =================
        {
            "part": 3,
            "passage": (
                "A man is calling a woman about a delayed shipment.\n"
                "The woman works in the delivery department."
            ),
            "content": "Why is the man calling the woman?",
            "choices": [
                ("To cancel an order", False),
                ("To ask about a delivery", True),
                ("To complain about a bill", False),
                ("To apply for a job", False),
            ]
        },
        {
            "part": 3,
            "passage": (
                "A man is calling a woman about a delayed shipment.\n"
                "The woman works in the delivery department."
            ),
            "content": "What will the woman do next?",
            "choices": [
                ("Contact the supplier", False),
                ("Check the order status", True),
                ("Issue a refund", False),
                ("Send a replacement", False),
            ]
        },

        # ================= PART 3 – Conversation 2 (2) =================
        {
            "part": 3,
            "passage": (
                "Two coworkers are discussing a team meeting scheduled for tomorrow.\n"
                "One of them will be out of the office."
            ),
            "content": "What are the speakers discussing?",
            "choices": [
                ("A job interview", False),
                ("A team meeting", True),
                ("A business trip", False),
                ("A training session", False),
            ]
        },
        {
            "part": 3,
            "passage": (
                "Two coworkers are discussing a team meeting scheduled for tomorrow.\n"
                "One of them will be out of the office."
            ),
            "content": "Why will one speaker miss the meeting?",
            "choices": [
                ("He is sick", False),
                ("He is on vacation", False),
                ("He has another appointment", True),
                ("He forgot about it", False),
            ]
        },

        # ================= PART 4 – Announcement 1 (2) =================
        {
            "part": 4,
            "passage": (
                "This is an announcement for passengers traveling on Flight 602.\n"
                "The flight has been delayed due to weather conditions."
            ),
            "content": "What is the announcement mainly about?",
            "choices": [
                ("A canceled flight", False),
                ("A delayed flight", True),
                ("A boarding change", False),
                ("A luggage issue", False),
            ]
        },
        {
            "part": 4,
            "passage": (
                "This is an announcement for passengers traveling on Flight 602.\n"
                "The flight has been delayed due to weather conditions."
            ),
            "content": "What are passengers asked to do?",
            "choices": [
                ("Leave the gate area", False),
                ("Wait near the gate", True),
                ("Change their tickets", False),
                ("Board immediately", False),
            ]
        },

        # ================= PART 4 – Announcement 2 (2) =================
        {
            "part": 4,
            "passage": (
                "The company cafeteria will be closed this Friday for maintenance.\n"
                "Employees may use nearby restaurants."
            ),
            "content": "What is being announced?",
            "choices": [
                ("A new cafeteria", False),
                ("A cafeteria closure", True),
                ("A company holiday", False),
                ("A menu change", False),
            ]
        },
        {
            "part": 4,
            "passage": (
                "The company cafeteria will be closed this Friday for maintenance.\n"
                "Employees may use nearby restaurants."
            ),
            "content": "What are employees advised to do?",
            "choices": [
                ("Bring their own food", False),
                ("Use nearby restaurants", True),
                ("Work from home", False),
                ("Leave early", False),
            ]
        },

        # ================= PART 5 (4) =================
        {
            "part": 5,
            "passage": None,
            "content": "The report must be completed _____ Friday.",
            "choices": [
                ("at", False),
                ("on", False),
                ("by", True),
                ("in", False),
            ]
        },
        {
            "part": 5,
            "passage": None,
            "content": "Ms. Lee is responsible _____ organizing the training session.",
            "choices": [
                ("of", False),
                ("for", True),
                ("with", False),
                ("to", False),
            ]
        },
        {
            "part": 5,
            "passage": None,
            "content": "The manager asked the staff to work _____ this weekend.",
            "choices": [
                ("additional", False),
                ("addition", False),
                ("additionally", True),
                ("add", False),
            ]
        },
        {
            "part": 5,
            "passage": None,
            "content": "All employees are required to attend the _____ meeting.",
            "choices": [
                ("annual", True),
                ("annually", False),
                ("annuity", False),
                ("announcing", False),
            ]
        },

        # ================= PART 6 (2) =================
        {
            "part": 6,
            "passage": (
                "Please review the attached document carefully.\n"
                "Make sure all information is correct before submitting the form."
            ),
            "content": "Please review the attached document _____ submitting the form.",
            "choices": [
                ("before", True),
                ("during", False),
                ("because", False),
                ("although", False),
            ]
        },
        {
            "part": 6,
            "passage": (
                "Please review the attached document carefully.\n"
                "Make sure all information is correct before submitting the form."
            ),
            "content": "What should be checked before submission?",
            "choices": [
                ("The delivery address", False),
                ("The document information", True),
                ("The meeting schedule", False),
                ("The payment method", False),
            ]
        },

        # ================= PART 7 (2) =================
        {
            "part": 7,
            "passage": (
                "NOTICE:\n"
                "The office will be closed all day Friday due to maintenance work."
            ),
            "content": "According to the notice, when will the office be closed?",
            "choices": [
                ("On Monday morning", False),
                ("All day Friday", True),
                ("During lunch time", False),
                ("On the weekend", False),
            ]
        },
        {
            "part": 7,
            "passage": (
                "NOTICE:\n"
                "The office will be closed all day Friday due to maintenance work."
            ),
            "content": "Why will the office be closed?",
            "choices": [
                ("A public holiday", False),
                ("Staff training", False),
                ("Maintenance work", True),
                ("A company event", False),
            ]
        },
    ]

    # Insert dữ liệu
    for q in questions_data:
        question = Question.objects.create(
            test=test,
            part=q["part"],
            passage=q["passage"],
            content=q["content"]
        )

        for content, is_correct in q["choices"]:
            Choice.objects.create(
                question=question,
                content=content,
                is_correct=is_correct
            )

    print("✅ Seed TOEIC Entrance Test (20 questions) SUCCESS")
