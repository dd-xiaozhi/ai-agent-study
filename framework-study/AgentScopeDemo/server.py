from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import json
import agentscope
from main import ThreeKingdomsWerewolfGame
from agentscope.message import Msg

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_client = None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global connected_client
    await websocket.accept()
    connected_client = websocket
    print("Client connected")
    try:
        while True:
            data = await websocket.receive_text()
            # Keep alive
    except WebSocketDisconnect:
        print("Client disconnected")
        connected_client = None

async def notify_frontend(msg):
    if connected_client:
        # Check if it's a special message or standard Msg
        if isinstance(msg, Msg):
            data = {
                "type": "msg",
                "name": msg.name,
                "content": str(msg.content),
                "role": getattr(msg, "role", "user")
            }
        else:
            data = msg # Assume dict
            
        await connected_client.send_text(json.dumps(data))

@app.post("/start")
async def start_game():
    # Check env vars
    if "OPENAI_API_KEY" not in os.environ:
        return {"status": "error", "message": "OPENAI_API_KEY not set"}
        
    asyncio.create_task(run_game_logic())
    return {"status": "started"}

async def run_game_logic():
    print("Starting game logic...")
    # Init agentscope
    agentscope.init()
    
    game = ThreeKingdomsWerewolfGame(notify_func=notify_frontend)
    
    # Patch setup_game to send player list
    original_setup = game.setup_game
    async def new_setup(*args, **kwargs):
        await original_setup(*args, **kwargs)
        # Send players
        players_data = []
        for p in game.alive_players:
            # Try to get role from game.roles
            role = game.roles.get(p.name, "未知")
            players_data.append({
                "name": p.name, 
                "role": role, 
                "status": "alive"
            })
            
        if connected_client:
            await connected_client.send_text(json.dumps({
                "type": "player_update", 
                "players": players_data
            }))
            
    game.setup_game = new_setup
    
    # Patch update_alive_players to send updates
    original_update = game.update_alive_players
    def new_update(dead_players):
        original_update(dead_players)
        # Send updated list
        players_data = []
        # Reconstruct list from all players (we need a full list to show dead ones)
        # game.players has all created agents
        for name, agent in game.players.items():
            is_alive = any(p.name == name for p in game.alive_players)
            role = game.roles.get(name, "未知")
            players_data.append({
                "name": name,
                "role": role,
                "status": "alive" if is_alive else "dead"
            })
            
        # We need to run async send in sync method? 
        # update_alive_players is sync in main.py
        # We can use asyncio.create_task since we are in async loop
        async def send_update():
            if connected_client:
                 await connected_client.send_text(json.dumps({
                    "type": "player_update", 
                    "players": players_data
                }))
        asyncio.create_task(send_update())

    game.update_alive_players = new_update

    await game.run_game()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
