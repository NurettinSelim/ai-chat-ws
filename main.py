import os
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
import uuid

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.chatrooms: List[Dict] = []
        self.messages: Dict[str, List[Dict]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: dict, room_id: str):
        if room_id not in self.messages:
            self.messages[room_id] = []
        self.messages[room_id].append(message)
        
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

    def create_chatroom(self, name: str) -> dict:
        room = {
            "id": str(uuid.uuid4()),
            "name": name
        }
        self.chatrooms.append(room)
        return room

    def get_chatroom(self, room_id: str) -> dict:
        return next((room for room in self.chatrooms if room["id"] == room_id), None)

    def get_room_messages(self, room_id: str) -> List[Dict]:
        return self.messages.get(room_id, [])

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get_rooms(request: Request):
    return templates.TemplateResponse("chatrooms.html", {"request": request})

@app.get("/chat/{room_id}", response_class=HTMLResponse)
async def get_chat(request: Request, room_id: str):
    room = manager.get_chatroom(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    return templates.TemplateResponse("chat.html", {"request": request, "room": room})

@app.get("/api/chatrooms")
async def get_chatrooms():
    return manager.chatrooms

@app.post("/api/chatrooms")
async def create_chatroom(room: dict):
    return manager.create_chatroom(room["name"])

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        messages = manager.get_room_messages(room_id)
        for message in messages:
            await websocket.send_json(message)

        while True:
            data = await websocket.receive_json()
            user_message = data["message"]
            
            await manager.broadcast({
                "sender": data["sender"],
                "message": user_message,
                "type": "user"
            }, room_id)

            messages = [HumanMessage(content=user_message)]
            ai_response = llm.invoke(messages)
            
            await manager.broadcast({
                "sender": "AI",
                "message": ai_response.content,
                "type": "ai"
            }, room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 