import requests
from datetime import datetime


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
        price_data['volume'] = float(data[0][5])

        return price_data

    return price_data
