# Jarvis AI — Testing Guide

## Running Tests
`ash
python -m pytest tests/ -v
`

## Test Structure
- 	est_actions.py — Task/reminder/note action handlers
- 	est_safety.py — Safety engine risk assessment
- 	est_llm_router.py — LLM provider routing
- 	est_api.py — REST API endpoints
- 	est_new_features.py — Expenses, habits, pomodoro, system monitor
- 	est_utils.py — Utility functions

## Writing New Tests
1. Create test file in 	ests/ directory
2. Use pytest fixtures and httpx.AsyncClient for API tests
3. Run full suite before submitting PR
