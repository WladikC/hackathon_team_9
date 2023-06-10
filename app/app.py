from flask import Flask, render_template
from flask_sock import Sock
from ret_prompt import generate_prompt
from news_fetcher import fetch_news
import openai
import os
import json
import time
from datetime import datetime, timedelta

from constants import PORTFOLIO

app = Flask(__name__)
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
sock = Sock(app)
openai.api_key = os.environ.get('OpenAPI_Key')


def generate_responses(start_time: str, minute_interval: int):
    """
    :param start_time: start time of when we want to do the backtest 'YYYY-mm-dd'
    :param minute_interval: integer which specifies how often we check for news
    """

    news_feed_start_time = datetime.strptime(start_time, "%Y-%m-%d") - timedelta(minutes=minute_interval)
    news_feed_end_time = datetime.strptime(start_time, "%Y-%m-%d")

    while True:
        news_feed_start_time += timedelta(minutes=minute_interval)
        news_feed_start_time = news_feed_start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        news_feed_end_time += timedelta(minutes=minute_interval)
        news_feed_end_time = news_feed_end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        stories = fetch_news(start_time=news_feed_start_time, end_time=news_feed_end_time)

        for coin in PORTFOLIO:
            print(f'Generating responses for {coin} news for date {news_feed_start_time}')
            news = get_news_for_coin(coin=coin, stories=stories)

            if news == '':
                continue

            result = generate_response(news=news, coin=coin)

        news_feed_start_time = datetime.strptime(news_feed_start_time, "%Y-%m-%dT%H:%M:%SZ")
        news_feed_end_time = datetime.strptime(news_feed_end_time, "%Y-%m-%dT%H:%M:%SZ")


def get_news_for_coin(coin: str, stories: dict) -> str:
    if len(stories[coin]) > 0:
        if len(stories[coin]) > 1:
            news = ''
            for i in range(len(stories[coin])):
                timestamp = list(stories[coin].keys())[i]
                news += stories[coin][timestamp]
        else:
            timestamp = list(stories[coin].keys())[0]
            news = stories[coin][timestamp]
    else:
        news = ''
        print('No news found.')

    return news


def generate_response(news: str, coin: str):
    prompt = generate_prompt(news=news, coin=coin)
    # Call the OpenAI API to generate a response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )

    # Get the generated response from the API
    try:
        generated_response = '{' + response.choices[0].text.strip().replace("\n", "").replace(" ", "").split('{')[1]
        response = json.loads(generated_response)
    except Exception as e:
        print(f'Formatting of response from ChatGPT not okay.'
              f'Response: {response}')
        return

    #Decide based on the response if to buy or sell a coin or do nothing.
    buy_or_sell = make_buy_or_sell_decision(coin=coin, message=generated_response)

    print(response)

    return buy_or_sell


def make_buy_or_sell_decision(coin: str, message: str):
    print('Make buy or sell decision.')
    print(message)
    message = json.loads(message)
    message = {key.lower(): value for key, value in message.items()}

    if 'positive' in message["pos_neg"].lower():
        buy_or_sell = [{"verdict": "Buy", "Coin": coin, "type": "coin"}]
    elif 'negative' in message["pos_neg"].lower():
        buy_or_sell = [{"verdict": "Sell", "Coin": coin, "type": "coin"}]
    else:
        buy_or_sell = [{"verdict": "Do nothing", "Coin": coin, "type": "coin"}]

    return buy_or_sell


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
