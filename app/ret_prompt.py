def generate_prompt(news: str, coin: str) -> str:
    prompt = f'''I want you to act as a financial advisor. I will give you a news article about {coin}, 
                 based on which you have to answer the following questions.
                 1. Will the impact on {coin} price be big or small or no impact? Please answer only 
                    with one of the three options.
                 2. Do you think the price of {coin} will be affected positively or negatively or not 
                    at all by this news? Please answer only with one of the three options. No further 
                    explanations needed. Generate the response in a json format with the keys: 
                    "impact", "pos_neg". Fill them with the answer to question 1 and question 2 
                    respectively. Give me only the json and nothing else. The news article is: 
                {news}
'''
    return prompt
