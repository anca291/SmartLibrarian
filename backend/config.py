import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DB_PATH = "./data/embeddings"
BOOKS_FILE_TXT = "./book_summaries.txt"
BOOKS_FILE_JSON = "./data/book_summaries.json"
