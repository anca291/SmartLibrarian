from fastapi import FastAPI
from routes import chat_routes

app = FastAPI()
app.include_router(chat_routes.router)

@app.get("/")
def root():
    return {"message": "Smart Librarian API is running"}
