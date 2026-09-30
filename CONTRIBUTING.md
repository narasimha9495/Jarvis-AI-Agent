# Contributing to Jarvis AI Agent

Thank you for your interest in contributing! Here's how to get started.

## 🚀 Quick Setup

```bash
# Clone the repo
git clone https://github.com/narasimha9495/Jarvis-AI-Agent.git
cd Jarvis-AI-Agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Run the app
python -m app.main
```

## 🧪 Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_new_features.py -v

# Run with coverage
python -m pytest tests/ --cov=app
```

## 📁 Project Structure

- `app/` — Backend (FastAPI + SQLAlchemy)
  - `actions/` — Feature modules (tasks, expenses, habits, etc.)
  - `api/` — REST routes and WebSocket handler
  - `core/` — LLM router, safety engine, STT/TTS
  - `providers/` — LLM provider implementations
  - `db/` — Database models and setup
  - `models/` — Pydantic schemas
- `frontend/` — Dashboard UI (HTML/JS)
- `tests/` — Test suite

## 🔧 Adding a New Action

1. Create `app/actions/your_action.py` extending `BaseAction`
2. Add DB models to `app/db/models.py` (if needed)
3. Register in `app/actions/__init__.py`
4. Add risk levels in `app/core/safety.py`
5. Add API routes in `app/api/routes.py`
6. Add to WebSocket handler in `app/api/websocket.py`
7. Write tests in `tests/`

## 📝 Code Style

- Python 3.11+ with type hints
- Async/await for all I/O
- Docstrings on all public classes and functions
- Use `logging` module (not `print()`)

## 🐛 Reporting Issues

Open an issue on GitHub with:
- What you expected
- What actually happened
- Steps to reproduce
