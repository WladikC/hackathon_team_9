def generate_prompt(news_string):
    prompt = f'''I want you to act as a financial advisor. I will give you a news article, based on which you have to answer the following questions.
            1. Will the impact on the instrument price be big or small. Please answer only with one of the two options for each of the affected companies.
            2. Do you think the price will be affected positively or negatively by this news. Please answer only with one of the two options for 
               each of the affected companies. No further explanations needed. 
            Generate the response in a json format with list of lists. Each list will contain 3 values; Bloomberg ticker symbol, answer to question 1 and question 2.
            The news article is 
            {news_string}'''
    return prompt