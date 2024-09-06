import openai

class GPTQueryProcessor:
    def __init__(self):
        openai.api_key = "your-openai-api-key"  # Replace with your actual key

    def convert_to_sql(self, question: str, data_columns):
        prompt = f"You are an expert in converting natural language to SQL queries. Given the following CSV columns: {', '.join(data_columns)}. Convert this question to a SQL query: {question}"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()