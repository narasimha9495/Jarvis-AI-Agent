# Adding a New Action to Jarvis

## 1. Create the handler
Create pp/actions/your_action.py:
`python
class YourAction:
    async def execute(self, params: dict) -> dict:
        # Your logic here
        return {"success": True, "message": "Done!"}
`

## 2. Register in safety engine
Add to ACTION_RISK_MAP in pp/core/safety.py.

## 3. Add WebSocket routing
The dispatcher in pp/api/websocket.py auto-discovers actions.

## 4. Write tests
Add tests in 	ests/test_your_action.py.
