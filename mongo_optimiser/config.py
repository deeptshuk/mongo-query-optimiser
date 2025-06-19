import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "test")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-7b-instruct")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
