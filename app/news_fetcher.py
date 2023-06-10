from __future__ import print_function
import aylien_news_api
from aylien_news_api.rest import ApiException
import os

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
