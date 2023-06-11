# AI Portfolio Manager

## Summary


## Running locally

Prepare .local-env file depending on your needs to be able to run the project locally
```
OpenAPI_Key=xxxx

AylienAPI_ID=xxxx
AylienAPI_Key=xxxx

START_TIME=YYYY-mm-dd
MINUTE_INTERVAL=60
MAXIMUM_PROMPT_LENGTH = 2000

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
