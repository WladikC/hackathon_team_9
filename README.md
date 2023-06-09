To build
docker build -t flowgptteam9 .

To run
docker run -it --env-file .local-env -p 8000:8000 -v $(pwd)/app/:/app flowgptteam9

.local-env file should contain your API key and any other environment variable that you need. The application starts on port 8000