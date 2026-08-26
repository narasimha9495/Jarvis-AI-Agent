# API Reference

## Health
- GET /api/health — Server status and available providers

## Tasks
- GET /api/tasks — List all tasks
- POST /api/tasks — Create a task
- PATCH /api/tasks/{id}/complete — Toggle task completion
- DELETE /api/tasks/{id} — Delete a task

## Reminders
- GET /api/reminders — List reminders
- POST /api/reminders — Create a reminder

## Notes
- GET /api/notes — List notes
- POST /api/notes — Create a note

## Expenses
- GET /api/expenses — List expenses with total
- POST /api/expenses — Add an expense

## Habits
- GET /api/habits — List habits with streaks
- POST /api/habits — Create a habit
- POST /api/habits/{id}/log — Log habit completion

## System
- GET /api/system/status — CPU, RAM, disk usage

## WebSocket
- ws://host/ws — Real-time chat interface
