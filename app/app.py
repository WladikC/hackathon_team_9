from flask import Flask, render_template
from flask_sock import Sock
from ret_prompt import generate_prompt
import openai
import os
import json
import time
from datetime import datetime, timedelta
import aylien_news_api
from aylien_news_api.rest import ApiException


app = Flask(__name__)
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
sock = Sock(app)
openai.api_key = os.environ.get('OpenAPI_Key')

MAXIMUM_PROMPT_LENGTH = 2000

PORTFOLIO = [
    "Bitcoin",
    "Ethereum",
    "Dogecoin",
    "Solana",
    "Binance Coin",
    "Cardano",
    "Polygon",
    "Litecoin",
    "Uniswap",
    "Avalanche",
]


class ResponseGenerator:
    def __init__(self):
        self.coin = ''
        self.news = ''

    @staticmethod
    def fetch_news(start_time: str, end_time: str) -> dict:
        """
        :param start_time: start of time range of published news in format YYYY-mm-ddTHH:MM:SSZ
        :param end_time: end of time range of published news in format YYYY-mm-ddTHH:MM:SSZ
        :return: news article summaries with publish times grouped by coins.
        """
        configuration = aylien_news_api.Configuration()
        configuration.api_key['X-AYLIEN-NewsAPI-Application-ID'] = os.getenv("AylienAPI_ID")
        configuration.api_key['X-AYLIEN-NewsAPI-Application-Key'] = os.getenv("AylienAPI_Key")
        configuration.host = "https://api.aylien.com/news"
        api_instance = aylien_news_api.DefaultApi(aylien_news_api.ApiClient(configuration))

        api_response = {}
        stories = {coin: {} for coin in PORTFOLIO}

        for coin in PORTFOLIO:
            print(f"fetching news for {coin}")
            opts = {
                'published_at_start': start_time,
                'published_at_end': end_time,
                'title': coin,
            }
            try:
                api_response[coin] = api_instance.list_stories(**opts)
            except ApiException as e:
                print("Exception when calling DefaultApi->list_stories: %s\n" % e)

            for i in range(len(api_response[coin].stories)):
                article_summary = ''
                publish_time = api_response[coin].stories[i].published_at.strftime("%Y-%m-%d %H:%M:%S")

                for j in range(len(api_response[coin].stories[i].summary.sentences)):
                    article_summary += api_response[coin].stories[i].summary.sentences[j]

                stories[coin][publish_time] = article_summary

        return stories

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

    def generate_response(self, news_feed_start_time: str, news_feed_end_time: str) -> list:
        stories = self.fetch_news(start_time=news_feed_start_time, end_time=news_feed_end_time)

        buy_or_sell_list = []
        for coin in PORTFOLIO:
            print(f'Generating responses for {coin} news for date {news_feed_start_time}')
            self.coin = coin
            self.news = self.get_news_for_coin(stories=stories)

            if self.news == '':
                continue

            if len(self.news) > MAXIMUM_PROMPT_LENGTH:
                self.news = self.news[:MAXIMUM_PROMPT_LENGTH]

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
                continue

            #Decide based on the response if to buy or sell a coin or do nothing.
            buy_or_sell = self.make_buy_or_sell_decision(message=generated_response)
            buy_or_sell_list.append(buy_or_sell)

        return buy_or_sell_list

    def make_buy_or_sell_decision(self, message: str):
        print('Make buy or sell decision.')
        print(message)
        message = json.loads(message)
        message = {key.lower(): value for key, value in message.items()}

        if 'positive' in message["pos_neg"].lower():
            buy_or_sell = json.dumps({"verdict": "Buy", "Coin": self.coin, "type": "coin"}) #"type": "coin"}]
        elif 'negative' in message["pos_neg"].lower():
            buy_or_sell = json.dumps({"verdict": "Sell", "Coin": self.coin, "type": "coin"}) #"type": "coin"}]
        else:
            buy_or_sell = json.dumps({"verdict": "Do nothing", "Coin": self.coin, "type": "coin"}) #"type": "coin"}]

        return buy_or_sell


def get_new_time_range(news_feed_start_time: datetime, news_feed_end_time: datetime, minute_interval: int):
    news_feed_start_time += timedelta(minutes=minute_interval)
    news_feed_start_time = news_feed_start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    news_feed_end_time += timedelta(minutes=minute_interval)
    news_feed_end_time = news_feed_end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    return news_feed_start_time, news_feed_end_time


# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')


@sock.route('/feed')
def feed(ws):
    start_time = os.getenv("START_TIME")
    minute_interval = int(os.getenv("MINUTE_INTERVAL"))

    response_generator = ResponseGenerator()

    news_feed_start_time = datetime.strptime(start_time, "%Y-%m-%d") - timedelta(minutes=minute_interval)
    news_feed_end_time = datetime.strptime(start_time, "%Y-%m-%d")

    while True:
        news_feed_start_time, news_feed_end_time = get_new_time_range(news_feed_start_time=news_feed_start_time, news_feed_end_time=news_feed_end_time, minute_interval=minute_interval)

        message = response_generator.generate_response(news_feed_start_time=news_feed_start_time, news_feed_end_time=news_feed_end_time)

        news_feed_start_time = datetime.strptime(news_feed_start_time, "%Y-%m-%dT%H:%M:%SZ")
        news_feed_end_time = datetime.strptime(news_feed_end_time, "%Y-%m-%dT%H:%M:%SZ")

        #message,porfoliovalue,outstandingcash = response_generator.generate_response() ## [{"verdict":"Buy","Coin":"BTC"},{"verdict":"Sell","Coin":"ETH"}],PortFolio Current Value, Outstanding Cash
        for msg in message:
            if "Buy" in msg or "Sell" in msg:
                ws.send(msg)
        time.sleep(5)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
