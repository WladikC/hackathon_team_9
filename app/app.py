from flask import Flask, request
import openai
import os
import json
app = Flask(__name__)

# Set up OpenAI API credentials
openai.api_key = os.environ.get('OpenAPI_Key')

def generate_prompt(news_string):
    prompt = f'''I want you to act as a financial advisor. I will give you a news article, based on which you have to answer the following questions.
            1. Will the impact on the instrument price be big or small. Please answer only with one of the two options for each of the affected companies.
            2. Do you think the price will be affected positively or negatively by this news. Please answer only with one of the two options for 
               each of the affected companies. No further explanations needed. 
            Generate the response in a json format with list of lists. Each list will contain 3 values; Bloomberg ticker symbol, answer to question 1 and question 2.
            The news article is 
            {news_string}'''
    return prompt
@app.route("/generate-response", methods=["GET"])
def generate_response():
    # Get the input string from the request
    input_string = '''EVgo Inc. sank 12% Friday, its worst day in nearly a month. ChargePoint Holdings, Inc. shed 13%, and Blink Charging Co. fell 11% for its largest daily loss since February. Beam Global, which designs clean energy systems for electric vehicle charging, slid 4.9%.
GM is the second major automaker to say it will use Tesla’s charging network. Ford Motor Co. announced a similar move in May. Tesla rose 4.1% on Friday, extending a $200 billion rally into an 11th day, while GM gained 1.1%.
While the pact is weighing heavily on other EV charging companies, the market may be overreacting, according to some on Wall Street.
“We think the news is overblown, though we would acknowledge that the news does put into question what GM is planning long-term with EVgo, which has been one of its key charging partners,” JPMorgan analyst Bill Peterson wrote in a note.
Read more: Tesla’s Record Run of Gains Drives $200 Billion Jump in Value
JPMorgan continues to see overweight-rated ChargePoint as well-positioned to benefit in areas where Tesla doesn’t compete, such as work, multifamily and fleet. They are less clear on EVgo’s direction in the long-term, but said the company continues to have significant partnerships with other EV makers including Toyota Motor Corp. and Subaru Corp. It’s likely that even given the news with Tesla, GM could take a multi-faceted approach in the future. JPMorgan has a neutral rating on EVgo.
Bank of America agrees that the news is more uncertain for EVgo, for which it has an underperform rating, even though GM identified an ongoing commitment to its eXtend business.
Read more: Tesla Set for $3 Billion Boost From Chargers at Rivals’ Expense
“We expect investors will be uneasy about competition as it now has another major partner,” BofA analyst Alex Vrabel said in a note. “In a more direct sense, given it is the site host, EVgo will now compete more directly for utilization against TSLA’s highly reliable network serving a larger piece of the future EV fleet.”
That’s not an issue for hardware-provider ChargePoint, as its network is largely fleet-focused, according to BofA, which reiterated its buy rating on the company.
Most Read from Bloomberg Businessweek'''

    inp2= '''After a period of relative calm, the United States '
                           'Securities and Exchange Commission (SEC) kicked '
                           'off its summer crypto crackdown by targeting two '
                           'major exchanges, Binance and Coinbase'''
    prompt = generate_prompt(inp2)
    # Call the OpenAI API to generate a response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )

    # Get the generated response from the API
    generated_response = response.choices[0].text.strip()
    print(response)
    return generated_response

if __name__ == "__main__":
     app.run(host="0.0.0.0", port=8000)