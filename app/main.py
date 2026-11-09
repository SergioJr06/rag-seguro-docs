from fastapi import FastAPI
from pydantic import BaseModel

from app.rag import ask

app = FastAPI(title="RAG Seguro Docs")


class Question(BaseModel):
    question: str
    k: int = 4


@app.post("/ask")
def ask_endpoint(q: Question):
    return ask(q.question, q.k)