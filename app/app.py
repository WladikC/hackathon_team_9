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


class ResponseGenerator:
    def __init__(self, start_time: str, minute_interval: int):
        self.start_time = start_time
        self.minute_interval = minute_interval
        self.coin = ''
        self.news = ''

    def generate_responses(self):
        news_feed_start_time = datetime.strptime(self.start_time, "%Y-%m-%d") - timedelta(minutes=self.minute_interval)
        news_feed_end_time = datetime.strptime(self.start_time, "%Y-%m-%d")

        while True:
            news_feed_start_time += timedelta(minutes=self.minute_interval)
            news_feed_start_time = news_feed_start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            news_feed_end_time += timedelta(minutes=self.minute_interval)
            news_feed_end_time = news_feed_end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            stories = fetch_news(start_time=news_feed_start_time, end_time=news_feed_end_time)

            for coin in PORTFOLIO:
                print(f'Generating responses for {coin} news for date {news_feed_start_time}')
                self.coin = coin
                self.news = self.get_news_for_coin(stories=stories)

                if self.news == '':
                    continue

                result = self.generate_response()

            news_feed_start_time = datetime.strptime(news_feed_start_time, "%Y-%m-%dT%H:%M:%SZ")
            news_feed_end_time = datetime.strptime(news_feed_end_time, "%Y-%m-%dT%H:%M:%SZ")

    def get_news_for_coin(self, stories: dict) -> str:
        if len(stories[self.coin]) > 0:
            if len(stories[self.coin]) > 1:
                news = ''
                for i in range(len(stories[self.coin])):
                    timestamp = list(stories[self.coin].keys())[i]
                    news += stories[self.coin][timestamp]
            else:
                timestamp = list(stories[self.coin].keys())[0]
                news = stories[self.coin][timestamp]
        else:
            news = ''
            print('No news found.')

        return news

    def generate_response(self):
        prompt = generate_prompt(news=self.news, coin=self.coin)
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
        buy_or_sell = self.make_buy_or_sell_decision(message=generated_response)

        print(response)

        return buy_or_sell

    def make_buy_or_sell_decision(self, message: str):
        print('Make buy or sell decision.')
        print(message)
        message = json.loads(message)
        message = {key.lower(): value for key, value in message.items()}

        if 'positive' in message["pos_neg"].lower():
            buy_or_sell = [{"verdict": "Buy", "Coin": self.coin, "type": "coin"}]
        elif 'negative' in message["pos_neg"].lower():
            buy_or_sell = [{"verdict": "Sell", "Coin": self.coin, "type": "coin"}]
        else:
            buy_or_sell = [{"verdict": "Do nothing", "Coin": self.coin, "type": "coin"}]

        return buy_or_sell


# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

@sock.route('/feed')
def feed(ws):
    #buytest = json.dumps({"verdict":"Buy","Coin":"BTC"})
    #selltest = json.dumps({"verdict":"Sell","Coin":"ETH"})
    start_time = os.getenv("START_TIME")
    minute_interval = os.getenv("MINUTE_INTERVAL")
    response_generator = ResponseGenerator(start_time=start_time, minute_interval=int(minute_interval))
    while True:
        message,porfoliovalue,outstandingcash = response_generator.generate_response() ## [{"verdict":"Buy","Coin":"BTC"},{"verdict":"Sell","Coin":"ETH"}],PortFolio Current Value, Outstanding Cash
        for msg in message:
            ws.send(msg)
        time.sleep(10)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
