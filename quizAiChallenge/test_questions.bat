@echo off
title Test Create Questions
cd /d e:\testDjangoWebSocket\chatTest\quizAiChallenge
call venv\Scripts\activate.bat
echo.
echo ========================================
echo Running Question Creation Test
echo ========================================
echo.
python test_create_questions.py
pause
