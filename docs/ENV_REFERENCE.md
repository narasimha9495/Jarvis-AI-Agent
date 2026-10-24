# Jarvis AI — Environment Variables

## Required
GEMINI_API_KEY=           # Google Gemini API key

## Optional Providers
OPENAI_API_KEY=           # OpenAI API key (if using OpenAI)
OLLAMA_HOST=              # Ollama server URL (default: http://localhost:11434)

## App Config
DEFAULT_PROVIDER=gemini   # gemini | openai | ollama
DATABASE_URL=sqlite:///./jarvis.db
LOG_LEVEL=info            # debug | info | warning | error
CORS_ORIGINS=*            # Comma-separated allowed origins

## Feature Flags
ENABLE_VOICE=false
ENABLE_SYSTEM_MONITOR=true
RATE_LIMIT_PER_MINUTE=60
