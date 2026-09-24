"""WebSocket endpoints for real-time communication."""

import json
import re
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.schemas import WebSocketMessage
from app.core.llm_router import LLMRouter
from app.core.safety import SafetyEngine
try:
    from app.actions import execute_action
except ImportError:
    # Dummy placeholder if module doesn't exist yet
    async def execute_action(action_name: str, params: dict, db: AsyncSession):
        return {"status": "mock_executed", "action": action_name}

ws_router = APIRouter()

SYSTEM_PROMPT = """You are Jarvis, a personal productivity AI assistant.
You can manage tasks, reminders, notes, and answer questions.
If you detect an action intent from the user, you MUST respond with a JSON object in this format:
{"action": "action_name", "params": {"param1": "value1", ...}}

Supported actions:
- create_task: {"title": str, "description": str, "priority": str}
- list_tasks: {}
- complete_task: {"task_id": int}
- create_reminder: {"message": str, "remind_at": str}
- list_reminders: {}
- create_note: {"title": str, "content": str, "tags": str}
- list_notes: {}
- search_web: {"query": str}

If no action is needed, just respond normally with a text message.
"""


def _extract_action(response: str) -> Optional[Dict[str, Any]]:
    """Helper to extract action JSON from LLM response."""
    try:
        # Check for JSON block markdown
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        json_str = match.group(1) if match else response
        
        # Try to parse the string as JSON
        data = json.loads(json_str)
        if isinstance(data, dict) and "action" in data:
            return data
    except Exception:
        pass
        
    return None


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """WebSocket endpoint for real-time interaction."""
    await websocket.accept()
    
    llm_router = LLMRouter()
    safety_engine = SafetyEngine()
    
    # Send welcome message
    welcome_msg = WebSocketMessage(
        type="chat",
        content="Hello! I am Jarvis. How can I help you today?"
    )
    await websocket.send_text(welcome_msg.model_dump_json())
    
    # In-memory history for simplicity in this file
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    try:
        while True:
            # Receive message from client
            text_data = await websocket.receive_text()
            
            try:
                data = json.loads(text_data)
                # Parse as WebSocketMessage
                msg = WebSocketMessage(**data)
            except Exception as e:
                error_msg = WebSocketMessage(type="status", content=f"Error parsing message: {str(e)}")
                await websocket.send_text(error_msg.model_dump_json())
                continue
                
            if msg.type == "chat":
                # Process chat message
                messages.append({"role": "user", "content": msg.content})
                
                try:
                    response_text = await llm_router.generate(
                        messages=messages,
                        provider=msg.provider
                    )
                    
                    messages.append({"role": "assistant", "content": response_text})
                    
                    # Extract potential action
                    action_data = _extract_action(response_text)
                    
                    if action_data:
                        action_name = action_data.get("action")
                        params = action_data.get("params", {})
                        
                        # Check safety
                        safety_check = await safety_engine.check_action(action_name, params)
                        
                        if not safety_check.allowed:
                            out_msg = WebSocketMessage(
                                type="status",
                                content=f"Action '{action_name}' blocked: {safety_check.message}"
                            )
                            await websocket.send_text(out_msg.model_dump_json())
                            continue
                            
                        if safety_check.requires_confirmation:
                            out_msg = WebSocketMessage(
                                type="confirm",
                                content=f"Confirmation required for: {action_name}. {safety_check.message}",
                                action=action_name,
                                params=params,
                                requires_confirmation=True
                            )
                            await websocket.send_text(out_msg.model_dump_json())
                            continue
                            
                        # If allowed and no confirmation, execute it directly
                        try:
                            result = await execute_action(action_name, params, db)
                            out_msg = WebSocketMessage(
                                type="action",
                                content=f"Executed action {action_name}",
                                action=action_name,
                                params={"result": result}
                            )
                            await websocket.send_text(out_msg.model_dump_json())
                        except Exception as e:
                            out_msg = WebSocketMessage(
                                type="status",
                                content=f"Failed to execute {action_name}: {str(e)}"
                            )
                            await websocket.send_text(out_msg.model_dump_json())
                    else:
                        # Normal text response
                        out_msg = WebSocketMessage(
                            type="chat",
                            content=response_text
                        )
                        await websocket.send_text(out_msg.model_dump_json())
                        
                except Exception as e:
                    error_msg = WebSocketMessage(type="status", content=f"Error generating response: {str(e)}")
                    await websocket.send_text(error_msg.model_dump_json())
                    
            elif msg.type == "confirm":
                if msg.action:
                    try:
                        result = await execute_action(msg.action, msg.params or {}, db)
                        out_msg = WebSocketMessage(
                            type="action",
                            content=f"Executed action {msg.action}",
                            action=msg.action,
                            params={"result": result}
                        )
                        await websocket.send_text(out_msg.model_dump_json())
                    except Exception as e:
                        out_msg = WebSocketMessage(
                            type="status",
                            content=f"Failed to execute confirmed action {msg.action}: {str(e)}"
                        )
                        await websocket.send_text(out_msg.model_dump_json())
                        
            elif msg.type == "status":
                status_msg = WebSocketMessage(
                    type="status",
                    content="System is online and running."
                )
                await websocket.send_text(status_msg.model_dump_json())
                
    except WebSocketDisconnect:
        # Handle disconnect clean up
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
