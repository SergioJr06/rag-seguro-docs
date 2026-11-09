import os

from dotenv import load_dotenv
from openai import OpenAI

from app.search import retrieve

load_dotenv()

SYSTEM_PROMPT = """You answer questions using ONLY the context between <context> tags.
- If the context does not contain the answer, reply exactly: "Não sei com base nos documentos."
- Cite sources as [file, p.N].
- Answer in the language of the question."""


def ask(question: str, k: int = 4) -> dict:
    hits = retrieve(question, k)
    context = "\n\n".join(f"[{h['source']}, p.{h['page']}]\n{h['text']}" for h in hits)

    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"<context>\n{context}\n</context>\n\nQuestion: {question}"},
        ],
    )
    return {
        "answer": resp.choices[0].message.content,
        "sources": [{"document": h["source"], "page": h["page"]} for h in hits],
    }