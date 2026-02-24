from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import convert, health, chat

load_dotenv(override=True)

app = FastAPI(title="DocuMind Local", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

app.include_router(convert.router, prefix="/convert", tags=["convert"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/")
def root():
    return {"status": "ok", "message": "DocuMind backend running"}
# AIzaSyDRwzd0MfXeg_5wSK0yTjqcp7Bhm79dsl4
