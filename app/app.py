from flask import Flask, render_template
from flask_socketio import SocketIO,emit
from ret_prompt import generate_prompt
from news_fetcher import fetch_news
from threading import Thread
import openai
import os
import json
import time

app = Flask(__name__)

# Set up OpenAI API credentials
openai.api_key = os.environ.get('OpenAPI_Key')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

def generate_response():
    inp2= fetch_news()
    prompt = generate_prompt(inp2)
    # Call the OpenAI API to generate a response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )

    # Get the generated response from the API
    generated_response = response.choices[0].text.strip()
    print(response)
    return generated_response
# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket event handler for client connection
@socketio.on(message='connect')
def on_connect():
    print('Client connected')
    
# WebSocket event handler for client disconnection
@socketio.on(message='disconnect')
def on_disconnect():
    print('Client disconnected')

def fetch_news_dummy():
    while True:
        # Simulate fetching news
        news = "This is some news fetched from the server"
        
        # Emit the news through WebSockets
        emit('news', {'news': news})
        time.sleep(5)
# Start the fetch_news function in a separate thread
def background_thread():
    fetch_news_dummy()

if __name__ == "__main__":
    socketio.start_background_task(background_thread)
    socketio.run(app,port=8000)