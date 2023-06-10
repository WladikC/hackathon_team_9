def generate_prompt(news: str, coin: str, price_data: dict) -> str:
    prompt = f"""I want you to act as a financial advisor. I will give you a news article about {coin} and also some 
                 financial data, based on which you have to answer the following questions.
                 1. Will the impact on {coin} price be big or small or no impact? Please answer only with one of 
                    the three options.
                 2. Do you think the price of {coin} will be affected positively or negatively or not at all 
                    by this news? Please answer only with one of the three options. No further explanations needed. 
                    Generate the response in a json format with the keys: "impact", "pos_neg". Fill them with 
                    the answer to question 1 and question 2 respectively. Give me only the json and nothing else. 
                    
                 The financial data are the following:
                 price 24 hours ago in USD: {price_data["open_price"]}
                 price now in USD: {price_data["close_price"]}
                 highest price in the last 24 hours in USD: {price_data["high_price"]}
                 lowest price in the last 24 hours in USD: {price_data["low_price"]}
                 traded volume in the last 24 hours in USD: {price_data["volume"]}
                 
                 The news article is:
                {news}
"""
    return prompt
