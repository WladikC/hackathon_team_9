from flask import Flask, render_template
from flask_sock import Sock
from ret_prompt import generate_prompt
from news_fetcher import fetch_news
from threading import Thread
import openai
import os
import json
import time

app = Flask(__name__)
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
sock = Sock(app)
openai.api_key = os.environ.get('OpenAPI_Key')

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
    list_of_buys_and_sells = parse_response(generated_response) #define this function
    Porfolio_value, Outstanding_Cash = execute_transactions(list_of_buys_and_sells) #define this
    return list_of_buys_and_sells,Porfolio_value,Outstanding_Cash
# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

@sock.route('/feed')
def feed(ws):
    buytest = json.dumps({"verdict":"Buy","Coin":"BTC"})
    selltest = json.dumps({"verdict":"Sell","Coin":"ETH"})
    while True:
        message,porfoliovalue,outstandingcash = generate_response() ## [{"verdict":"Buy","Coin":"BTC"},{"verdict":"Sell","Coin":"ETH"}],PortFolio Current Value, Outstanding Cash
        for msg in message:
            ws.send(msg)
        time.sleep(10)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)