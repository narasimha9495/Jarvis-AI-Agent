# Frequently Asked Questions

## How do I add my API key?
Copy .env.example to .env and paste your Gemini API key.

## Can I use OpenAI instead of Gemini?
Yes! Set DEFAULT_PROVIDER=openai in .env and add your OpenAI key.

## How do I run tests?
`ash
python -m pytest tests/ -v
`

## Is my data stored locally?
Yes, all data stays in a local SQLite database. Nothing is sent to external servers except LLM queries.
