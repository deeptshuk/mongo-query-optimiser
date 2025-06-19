from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class Request(BaseModel):
    model: str
    messages: List[Message]

@app.post("/api/v1/chat/completions")
def completions(req: Request):
    return {
        "choices": [
            {
                "message": {
                    "content": "Mocked LLM recommendation for query optimization."
                }
            }
        ]
    }
