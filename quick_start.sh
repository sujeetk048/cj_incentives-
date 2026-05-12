#!/bin/bash
# Quick Start Script for Incentive Automation System
# This script helps you get started quickly

echo "========================================"
echo "Incentive Automation System - Quick Start"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[1/4] Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env file with your Snowflake credentials!"
    read -p "Press Enter to continue after editing .env..."
else
    echo "[1/4] .env file already exists."
fi

echo ""
echo "[2/4] Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "[3/4] Creating logs directory..."
mkdir -p logs

echo ""
echo "[4/4] Ready to run!"
echo ""
echo "Choose an option:"
echo "  1. Run once (single execution)"
echo "  2. Run with scheduler (continuous)"
echo "  3. Start web dashboard"
echo "  4. Exit"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Running single execution..."
        python main.py --mode once
        ;;
    2)
        echo ""
        echo "Starting scheduled execution..."
        echo "Press Ctrl+C to stop."
        python main.py --mode scheduled
        ;;
    3)
        echo ""
        echo "Starting web dashboard..."
        echo "Open http://localhost:5000 in your browser."
        python app.py
        ;;
    4)
        echo "Exiting."
        ;;
    *)
        echo "Invalid choice. Exiting."
        ;;
esac
