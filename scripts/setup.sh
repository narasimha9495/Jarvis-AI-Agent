#!/bin/bash
set -e
echo 'Setting up Jarvis AI Agent...'
[ ! -d 'venv' ] && python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
[ ! -f '.env' ] && cp .env.example .env
echo 'Setup complete! Run: uvicorn app.main:app --reload'
