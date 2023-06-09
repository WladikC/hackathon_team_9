from flask import Flask, request
import openai
import os
app = Flask(__name__)

# Set up OpenAI API credentials
openai.api_key = os.environ.get('OpenAPI_Key')

@app.route("/generate-response", methods=["GET"])
def generate_response():
    # Get the input string from the request
    input_string = "hi what can you do"

    # Call the OpenAI API to generate a response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=input_string,
        max_tokens=100
    )

    # Get the generated response from the API
    generated_response = response.choices[0].text.strip()

    return generated_response

if __name__ == "__main__":
     app.run(host="0.0.0.0", port=8000)