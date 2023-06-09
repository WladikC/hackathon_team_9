# hackathon_team_9

## Prerequisites
Python == 3.9

Poetry >= 1.3.2

## Running locally
Docker image can be built locally using command
```
sudo docker build -t hackathon:latest -f Dockerfile .
```

Prepare .local-env file for running project locally depending on your needs.

Running example job by executing
```
sudo docker run --env-file .local-env hackathon:latest poetry run example <variable1> <variable2>
```