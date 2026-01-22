@echo off
title Test AI Worker Direct
cd /d e:\testDjangoWebSocket\chatTest\quizAiChallenge
call venv\Scripts\activate.bat
echo.
echo ========================================
echo Test AI Worker Direct (Ngrok)
echo ========================================
echo.
python test_ai_direct.py
echo.
pause
