import openai
from config import OPENAI_API_KEY

class GPTService:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY

    def get_recommendation(self, context: str, query: str) -> str:
        prompt = f"Pe baza acestui context: {context}\nRăspunde la întrebarea: {query}\n"
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ești un asistent care recomandă cărți pe baza contextului."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message["content"]
