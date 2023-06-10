from flask import Flask, render_template
from flask_sock import Sock
from ret_prompt import generate_prompt
import openai
import requests
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
START_CAPITAL = 100000
BUY_BIG_PERCENTAGE = 10
BUY_SMALL_PERCENTAGE = 5
SELL_SMALL_PERCENTAGE = 20
TRADING_FEES_BIPS = 10
BID_ASK_SPREAD_BIPS = 10

PORTFOLIO = {
    "Bitcoin": "BTCUSDT",
    "Ethereum": "ETHUSDT",
    "Dogecoin": "DOGEUSDT",
    "Solana": "SOLUSDT",
    "Binance Coin": "BNBUSDT",
    "Cardano": "ADAUSDT",
    "Polygon": "MATICUSDT",
    "Litecoin": "LTCUSDT",
    "Uniswap": "UNIUSDT",
    "Avalanche": "AVAXUSDT"
}


class AIPortfolioManager:
    def __init__(self):
        self.coin = None
        self.news = None
        self.prices = {}
        self.positions = {coin: 0 for coin in PORTFOLIO.keys()}
        self.positions['Cash'] = START_CAPITAL
        self.portfolio_value = START_CAPITAL

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
        stories = {coin: {} for coin in PORTFOLIO.keys()}

        for coin in PORTFOLIO.keys():
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

    def generate_response(self, news_feed_start_time: str, news_feed_end_time: str) -> (list, float, float):
        stories = self.fetch_news(start_time=news_feed_start_time, end_time=news_feed_end_time)

        buy_or_sell_list = []
        for coin in PORTFOLIO.keys():
            print(f'Generating responses for {coin} news for date {news_feed_start_time}')
            self.coin = coin
            self.news = self.get_news_for_coin(stories=stories)

            symbol = PORTFOLIO[self.coin]
            price_data = self.get_currency_price_data(timestamp=datetime.strptime(news_feed_end_time, "%Y-%m-%dT%H:%M:%SZ"), symbol=symbol)

            if price_data.get("close_price") is None:
                print("No price available.")
                continue

            self.prices[self.coin] = price_data.get("close_price")

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

            # Decide based on the response if to buy or sell a coin or do nothing.
            buy_or_sell = self.make_buy_or_sell_decision(message=generated_response)
            if buy_or_sell["verdict"] in ["Buy", "Sell"]:
                buy_or_sell_list.append(buy_or_sell)

        # In order to do the sells first.
        buy_or_sell_list = sorted(buy_or_sell_list, key=lambda x: x["verdict"], reverse=True)

        self.do_transactions_and_calculate_new_positions(buy_or_sell_list=buy_or_sell_list)
        self.calculate_portfolio_value()

        buy_or_sell_list = [json.dumps(x) for x in buy_or_sell_list]

        return buy_or_sell_list, self.portfolio_value, self.positions['Cash']

    def do_transactions_and_calculate_new_positions(self, buy_or_sell_list: list):
        for signals in buy_or_sell_list:
            buy_sell = signals["verdict"]
            coin = signals["Coin"]

            if buy_sell == "Sell":
                if self.positions[coin] > 0:
                    sell_price = self.prices[coin] * (1 - (TRADING_FEES_BIPS + BID_ASK_SPREAD_BIPS/2)/10000)
                    self.positions['Cash'] += round(self.positions[coin] * sell_price, 2)
                    self.positions[coin] = 0

            elif buy_sell == "Buy":
                buy_price = self.prices[coin] * (1 + (TRADING_FEES_BIPS + BID_ASK_SPREAD_BIPS/2)/10000)
                self.positions['Cash'] -= round(BUY_SMALL_PERCENTAGE/100 * self.positions['Cash'], 2)
                self.positions[coin] += round(BUY_SMALL_PERCENTAGE/100 * self.positions['Cash'] / buy_price, 5)

    def calculate_portfolio_value(self):
        coin_value = 0
        for coin in PORTFOLIO.keys():
            coin_value += self.positions[coin] * self.prices[coin]

        self.portfolio_value = self.positions['Cash'] + coin_value
        print(f"Portfolio value: {self.portfolio_value}")

    def make_buy_or_sell_decision(self, message: str):
        print('Make buy or sell decision.')
        message = json.loads(message)
        message = {key.lower(): value for key, value in message.items()}

        if 'positive' in message["pos_neg"].lower():
            buy_or_sell = {"verdict": "Buy", "Coin": self.coin, "type": "coin"}
        elif 'negative' in message["pos_neg"].lower():
            buy_or_sell = {"verdict": "Sell", "Coin": self.coin, "type": "coin"}
        else:
            buy_or_sell = {"verdict": "Do nothing", "Coin": self.coin, "type": "coin"}

        return buy_or_sell

    @staticmethod
    def get_currency_price_data(timestamp: datetime, symbol: str) -> dict:
        """
        :param timestamp: time for which the price should be retrieved as datetime object
        :param symbol: symbol for which the price should be retrieved as string
        :return: dictionary which includes open price, high price, low price, close price
                 and volume for the given symbol and the last 24h period before the given timestamp.
        """

        url = "https://api.binance.com/api/v3/klines"

        params = {
            "symbol": symbol,
            "interval": "1d",
            "startTime": int(datetime.timestamp(timestamp) * 1000),
            "limit": 1,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        price_data = {}

        if len(data) > 0:
            price_data['open_price'] = float(data[0][1])
            price_data['high_price'] = float(data[0][2])
            price_data['low_price'] = float(data[0][3])
            price_data['close_price'] = float(data[0][4])
            price_data['volume'] = float(data[0][5]) * float(data[0][4])

            return price_data

        return price_data


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

    ai_portfolio_manager = AIPortfolioManager()

    news_feed_start_time = datetime.strptime(start_time, "%Y-%m-%d") - timedelta(minutes=minute_interval)
    news_feed_end_time = datetime.strptime(start_time, "%Y-%m-%d")

    while True:
        news_feed_start_time, news_feed_end_time = get_new_time_range(news_feed_start_time=news_feed_start_time, news_feed_end_time=news_feed_end_time, minute_interval=minute_interval)

        message, portfolio_value, outstanding_cash = ai_portfolio_manager.generate_response(news_feed_start_time=news_feed_start_time, news_feed_end_time=news_feed_end_time)

        news_feed_start_time = datetime.strptime(news_feed_start_time, "%Y-%m-%dT%H:%M:%SZ")
        news_feed_end_time = datetime.strptime(news_feed_end_time, "%Y-%m-%dT%H:%M:%SZ")

        for msg in message:
            ws.send(msg)
        time.sleep(5)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
