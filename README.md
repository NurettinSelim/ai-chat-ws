# AI Chat Room with Gemini

A real-time chat application where multiple users can interact with Google's Gemini AI model in a shared chat room.

## Features
- Real-time chat using WebSockets
- Multiple users can join the chat room
- Shared chat history for all users
- Integration with Google's Gemini AI model
- Clean and modern UI

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

3. Run the application:
```bash
python main.py
```

4. Open your browser and navigate to `http://localhost:8000`

## Usage
1. Enter your name in the username field
2. Type your message in the input field
3. Press Enter or click Send to send your message
4. The AI will respond to your message, and all connected users will see the conversation

## Technologies Used
- FastAPI
- WebSockets
- LangChain
- Google Gemini AI
- HTML/CSS/JavaScript 