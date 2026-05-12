@echo off
REM Quick Start Script for Incentive Automation System
REM This script helps you get started quickly

echo ========================================
echo Incentive Automation System - Quick Start
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [1/4] Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env file with your Snowflake credentials!
    echo Press any key to continue after editing .env...
    pause > nul
) else (
    echo [1/4] .env file already exists.
)

echo.
echo [2/4] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [3/4] Creating logs directory...
if not exist logs mkdir logs

echo.
echo [4/4] Ready to run!
echo.
echo Choose an option:
echo   1. Run once (single execution)
echo   2. Run with scheduler (continuous)
echo   3. Start web dashboard
echo   4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running single execution...
    python main.py --mode once
) else if "%choice%"=="2" (
    echo.
    echo Starting scheduled execution...
    echo Press Ctrl+C to stop.
    python main.py --mode scheduled
) else if "%choice%"=="3" (
    echo.
    echo Starting web dashboard...
    echo Open http://localhost:5000 in your browser.
    python app.py
) else (
    echo Exiting.
)

echo.
pause
