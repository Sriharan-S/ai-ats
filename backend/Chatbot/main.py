import json
import requests
from flask import Flask, render_template,request
from flask_socketio import SocketIO, emit
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

API_KEY = "e3244ff8d3b5b0f2b3449367f53de72ca407c29296bc69f9c1a7679d5ba6a6b5"  # Replace with your valid API key
URL = "https://api.together.xyz/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def ask_together(prompt, sid):
    """Query Together.AI with streaming enabled and send responses in real-time."""
    data = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",
        "messages": [{"role": "user", "content": prompt}],
        "stream": True  # Enable real-time streaming
    }

    try:
        response = requests.post(URL, json=data, headers=HEADERS, stream=True)
        response.raise_for_status()

        collected_text = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line.decode("utf-8").strip())
                    if "choices" in json_line and json_line["choices"]:
                        token = json_line["choices"][0]["delta"].get("content", "")
                        if token:
                            collected_text += token
                            socketio.emit('response', {'reply': token}, room=sid)  # Send tokens dynamically
                except json.JSONDecodeError:
                    continue  # Skip invalid JSON data
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        socketio.emit('response', {'reply': f"Error: {str(e)}"}, room=sid)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    """Handle user message and return chatbot response."""
    user_query = data['message']
    sid = request.sid  # Get user session ID for private messaging
    print(f"User ({sid}): {user_query}")  # ✅ Debugging output
    threading.Thread(target=ask_together, args=(user_query, sid)).start()  # Run in a new thread

if __name__ == '__main__':
    socketio.run(app, port=1000, debug=True, allow_unsafe_werkzeug=True)
