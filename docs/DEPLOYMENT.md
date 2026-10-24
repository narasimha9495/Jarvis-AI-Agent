# Deployment Guide

## Docker
`ash
docker build -t jarvis-ai .
docker run -p 8000:8000 --env-file .env jarvis-ai
`

## Docker Compose
`ash
docker-compose up -d
`

## Manual
`ash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
`

## Production Tips
- Use --workers 4 for multi-core utilisation
- Set LOG_LEVEL=warning to reduce noise
- Use a reverse proxy (nginx) for HTTPS
