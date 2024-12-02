import os
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage

# Load environment variables
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7,
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.chat_history: List[Dict] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        self.chat_history.append(message)
        for connection in self.active_connections:
            await connection.send_json(message)

    def get_chat_history(self):
        return self.chat_history

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send chat history to new connection
        for message in manager.get_chat_history():
            await websocket.send_json(message)

        while True:
            data = await websocket.receive_json()
            user_message = data["message"]
            
            # Broadcast user message
            await manager.broadcast({
                "sender": data["sender"],
                "message": user_message,
                "type": "user"
            })

            # Get AI response
            messages = [HumanMessage(content=user_message)]
            ai_response = llm.invoke(messages)
            
            # Broadcast AI response
            await manager.broadcast({
                "sender": "AI",
                "message": ai_response.content,
                "type": "ai"
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 