# AI Portfolio Manager
This tool uses Large Language Models (LLM) to make buy or sell decisions 
in the crypto space, based on news articles and basic financial data. It is important to mention 
that it doesn't do actual trades, but rather simulates trades based on the decisions
and tracks the performance of the portfolio on a simple frontend page.

Note: The strategy has much potential for improvement. This tool provides the architecture to implement 
other strategies as well as prompts, and test them.

## API's used
* Aylien News API: to fetch news articles
* Binance API: to get basic financial data about coins
* OpenAI API: to interact with ChatGPT

## Functionality
Every hour the following steps are happening:
1. For every coin in our Portfolio fetch the news from the last hour.
   If there are multiple news articles for a coin, combine them to one.
2. For every coin fetch 1 hour klines from Binance (open price, close price,
   high price, low price, volume).
3. Use the data from 1. and 2. in a predefined prompt, which generates 
   a response from OpenAI API. The response tells us whether the effect on 
   the coin price will be positive, negative or neutral, and whether 
   the impact will be small or big.
4. Based on the response do a decision, whether to buy or sell, and in which quantity. 
   Our strategy is a long only strategy, so it will not sell
   when there are no positions of the corresponding coin in the portfolio.
5. Simulate transactions, calculate new position sizes and new portfolio value.
6. Send the done trades and portfolio value via websocket to the frontend page.

## How to adjust the portfolio
If you want to add or remove certain coins to/from the portfolio,
you can do that by adjusting the PORTFOLIO variable in app.py.
The variable is a dictionary with coin names as keys and the 
corresponding Binance-Symbol for the coin-USDT currency pair.


## Running locally

Prepare .local-env file depending on your needs to be able to run the project locally
```
OpenAPI_Key=xxxx

AylienAPI_ID=xxxx
AylienAPI_Key=xxxx

START_TIME=2023-05-09
MINUTE_INTERVAL=60  # leave it at that value
MAXIMUM_PROMPT_LENGTH = 2000 # leave it at that value

START_CAPITAL = 100000
BUY_BIG_PERCENTAGE = 10 # Percentage of Cash used for big impact positive news
BUY_SMALL_PERCENTAGE = 5 # Percentage of Cash used for small impact  positive news
SELL_SMALL_PERCENTAGE = 20 # Percentage of positions to be sold for small impact  negative news
SELL_BIG_PERCENTAGE = 100 # Percentage of positions to be sold for big impact  negative news
TRADING_FEES_BIPS = 10 
BID_ASK_SPREAD_BIPS = 10 

BUY_ON_BAD_NEWS=false # when set to true, it will do the opposite of what the LLM suggests
```

Docker image can be built using command
```
docker build -t flowgptteam9 .
```

The job can be run using the command
```
docker run -it --env-file .local-env -p 8000:8000 -v $(pwd)/app/:/app flowgptteam9
```
The application starts on Port 8000.
