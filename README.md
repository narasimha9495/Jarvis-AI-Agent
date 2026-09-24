# 🤖 Jarvis AI Agent

A modular, privacy-first personal productivity AI assistant built with **FastAPI**, **WebSocket**, and multi-provider LLM support.

> **What problem does this solve?**  
> A single AI interface to manage your tasks, reminders, notes, and web searches — running safely on your machine with confirmation before risky actions, and working with multiple LLM providers (including offline via Ollama).

---

## ✨ Features

- **Multi-Provider LLM Support** — Switch between Google Gemini, OpenAI, and Ollama (local/offline)
- **Real-time Chat** — WebSocket-powered live conversation with your AI assistant
- **Task Management** — Create, list, complete, and delete personal tasks
- **Reminders** — Set time-based reminders with natural language
- **Quick Notes** — Create and search notes with tags
- **Web Search** — Search the web via DuckDuckGo (no API key needed)
- **Safety Engine** — Risk-level assessment with confirmation for destructive actions
- **Privacy-First** — Local STT (Whisper), local TTS (pyttsx3), secrets in `.env`
- **Modern Dashboard** — Iron Man Jarvis-inspired dark UI with real-time updates

---

## 🏗️ Architecture

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Settings via .env
├── api/
│   ├── routes.py        # REST endpoints
│   └── websocket.py     # Real-time WebSocket handler
├── core/
│   ├── llm_router.py    # Multi-provider LLM routing
│   ├── safety.py        # Risk assessment engine
│   ├── stt.py           # Speech-to-text (Whisper, local)
│   └── tts.py           # Text-to-speech (pyttsx3, local)
├── providers/
│   ├── base.py          # Abstract LLM provider
│   ├── gemini_provider.py
│   ├── openai_provider.py
│   └── ollama_provider.py
├── actions/
│   ├── tasks.py         # Task CRUD
│   ├── reminders.py     # Reminder management
│   ├── notes.py         # Notes with search
│   └── search.py        # Web search
├── db/
│   ├── database.py      # Async SQLite setup
│   └── models.py        # SQLAlchemy models
└── models/
    └── schemas.py       # Pydantic v2 schemas

frontend/
├── index.html           # Dashboard UI
└── js/
    └── app.js           # WebSocket client & UI logic

tests/
├── test_safety.py       # Safety engine tests
├── test_actions.py      # Action module tests
├── test_llm_router.py   # LLM router tests
└── test_api.py          # API endpoint tests
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/narasimha9495/Jarvis-AI-Agent.git
cd Jarvis-AI-Agent
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run

```bash
python -m app.main
# Open http://localhost:8000 in your browser
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and set your keys:

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | For Gemini provider |
| `OPENAI_API_KEY` | OpenAI API key | For OpenAI provider |
| `OLLAMA_BASE_URL` | Ollama server URL | For local/offline LLM |
| `DEFAULT_LLM_PROVIDER` | Default: `gemini` | No |

> **Offline Mode**: Set `DEFAULT_LLM_PROVIDER=ollama` and run [Ollama](https://ollama.ai) locally. No API keys needed.

---

## 🛡️ Safety Engine

Every action is classified by risk level:

| Risk Level | Actions | Behavior |
|------------|---------|----------|
| ✅ **Safe** | List tasks, search, read notes | Execute immediately |
| ⚠️ **Moderate** | Create task, set reminder | Execute with notification |
| 🔴 **Dangerous** | Delete task, delete note | Requires user confirmation |
| 🚫 **Blocked** | Shell commands, system access | Always denied |

The assistant **never** runs shell commands or accesses your system directly.

---

## 🧪 Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## 🔌 LLM Providers

| Provider | Requires API Key | Offline | Setup |
|----------|-----------------|---------|-------|
| **Gemini** | Yes | No | Add `GEMINI_API_KEY` to `.env` |
| **OpenAI** | Yes | No | Add `OPENAI_API_KEY` to `.env` |
| **Ollama** | No | Yes | Install [Ollama](https://ollama.ai) and run `ollama pull llama3.2` |

Switch providers in real-time from the dashboard dropdown or via API.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check + available providers |
| `POST` | `/api/chat` | Send a chat message |
| `GET` | `/api/tasks` | List all tasks |
| `POST` | `/api/tasks` | Create a task |
| `PATCH` | `/api/tasks/{id}/complete` | Complete a task |
| `DELETE` | `/api/tasks/{id}` | Delete a task |
| `GET` | `/api/reminders` | List reminders |
| `POST` | `/api/reminders` | Create a reminder |
| `GET` | `/api/notes` | List notes |
| `POST` | `/api/notes` | Create a note |
| `WS` | `/ws` | Real-time WebSocket chat |

Full interactive docs at `/docs` (Swagger UI).

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Frontend**: Vanilla HTML/CSS/JS (no framework)
- **Database**: SQLite + SQLAlchemy (async)
- **LLM**: google-generativeai, openai, ollama
- **STT**: OpenAI Whisper (local)
- **TTS**: pyttsx3 (local/offline)
- **Testing**: pytest + pytest-asyncio

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
