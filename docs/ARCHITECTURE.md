# Architecture Overview

Jarvis uses a modular architecture with clear separation of concerns.

## Components
- **app/core/** — LLM router, safety engine, config
- **app/providers/** — Pluggable LLM backends (Gemini, OpenAI, Ollama)
- **app/actions/** — Business logic handlers for each action type
- **app/api/** — REST + WebSocket endpoints
- **app/db/** — SQLAlchemy models and session management
- **frontend/** — Vanilla JS single-page dashboard

## Request Flow
1. User sends message via WebSocket
2. LLM Router selects provider and generates response
3. Safety Engine checks action risk level
4. Action handler executes and returns result
5. Response sent back via WebSocket
