from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
from typing import Dict, Optional
from datetime import datetime

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your iOS app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store connected Windows clients
clients: Dict[str, WebSocket] = {}

class CommandData(BaseModel):
    headphones: bool
    microphone: bool
    killApp: bool
    reboot: bool

@app.get("/")
async def root():
    return {
        "status": "running",
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "clients_connected": len(clients)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = str(id(websocket))
    clients[client_id] = websocket
    
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        del clients[client_id]

@app.post("/command")
async def send_command(command: CommandData):
    if not clients:
        return {
            "status": "error",
            "message": "No Windows clients connected",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # Convert command to JSON
    command_json = command.json()
    
    # Send to all connected Windows clients
    failed_clients = []
    success_count = 0
    
    for client_id, client_ws in list(clients.items()):
        try:
            await client_ws.send_text(command_json)
            success_count += 1
        except:
            failed_clients.append(client_id)
            del clients[client_id]
    
    return {
        "status": "success",
        "message": f"Command sent to {success_count} clients",
        "failed_clients": len(failed_clients),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
