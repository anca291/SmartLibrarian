import logging
from fastapi import FastAPI
from routes import chat_routes
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # or set to ['*'] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_routes.router)

@app.get("/")
def root():
    logging.info("[BACKEND] Server is running")
    return {"message": "Smart Librarian API is running"}

@app.get("/ping")
def ping():
    print("[BACKEND] /ping a fost apelat")
    return {"pong": True}