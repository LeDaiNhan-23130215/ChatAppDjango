@echo off
title AI Worker Test
cd /d e:\testDjangoWebSocket\chatTest\quizAiChallenge
call venv\Scripts\activate.bat
echo.
echo ========================================
echo Testing AI Worker Endpoints
echo ========================================
echo.
python test_ai_worker.py
echo.
pause
