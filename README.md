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

## Adding a new Python dependency
Use the command
```
poetry add <package>
```
Poetry will install the package, take care of dependencies and update the poetry.lock file.

## Adding new jobs
1. Add the function that your job will run, in the pyproject.toml file under [tool.poetry.scripts] and give it a name, similar to the example job.
2. You can run it with docker by using the command

```
sudo docker run --env-file .local-env hackathon:latest poetry run <name of your job as in pyproject.toml> <input variables seperated by a space>
```