from openai import OpenAI
from langdetect import detect
from config import OPENAI_API_KEY

class GPTService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except:
            return "ro"

    def get_recommendation(self, context: str, query: str) -> str:
        lang = self.detect_language(query)
        if lang == "ro":
            system_message = "Ești un asistent care recomandă cărți. Răspunde mereu în limba română."
        else:
            system_message = "You are an assistant that recommends books. Always respond in English."

        prompt = f"Context: {context}\nÎntrebare utilizator: {query}"

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
