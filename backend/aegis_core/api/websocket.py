"""
Aegis AI - Real-time WebSocket Protocol Gateway.
Provides token-by-token streaming, tool telemetry, and interactive confirmation cards to the HUD.
"""

import json
from typing import Any, Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from aegis_core.agent.planner import agent_planner
from aegis_core.utils.logger import logger

ws_router = APIRouter()
_active_websockets: Set[WebSocket] = set()


async def broadcast_ws_event(event: Dict[str, Any]) -> None:
    """Broadcasts real-time events (e.g. reminder alerts) to all connected HUD clients."""
    for ws in list(_active_websockets):
        try:
            await ws.send_json(event)
        except Exception:
            _active_websockets.discard(ws)


@ws_router.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """Bidirectional WebSocket connection for live desktop assistant interactions."""
    await websocket.accept()
    _active_websockets.add(websocket)
    logger.info("WebSocket client connected to session: %s", session_id)

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON payload."})
                continue

            msg_type = data.get("type", "user_message")

            # Heartbeat ping
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "user_message":
                prompt = data.get("content", "").strip()
                user_confirmed = bool(data.get("user_confirmed", False))

                if not prompt:
                    await websocket.send_json({"type": "error", "message": "Prompt cannot be empty."})
                    continue

                try:
                    async for event in agent_planner.execute_task(
                        user_prompt=prompt,
                        session_id=session_id,
                        user_confirmed=user_confirmed,
                    ):
                        await websocket.send_json(event)
                except Exception as exc:
                    logger.error("Error processing agent task: %s", exc, exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Processing error: {str(exc)}",
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from session: %s", session_id)
    except Exception as exc:
        logger.error("Unexpected WebSocket error: %s", exc, exc_info=True)
    finally:
        _active_websockets.discard(websocket)
