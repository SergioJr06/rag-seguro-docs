from fastapi.testclient import TestClient

from app import main, rag
from app.ingest import chunk_text
from app.search import retrieve


def test_chunk_text_respeita_tamanho():
    chunks = chunk_text("a" * 2000, size=700, overlap=100)
    assert len(chunks) > 1
    assert all(len(c) <= 700 for c in chunks)


def test_chunk_text_vazio():
    assert chunk_text("") == []


def test_retrieve_devolve_fontes():
    hits = retrieve("What is prompt injection?", k=4)
    assert len(hits) == 4
    assert all("source" in h and "page" in h for h in hits)


def test_endpoint_ask(monkeypatch):
    fake = {"answer": "ok", "sources": [{"document": "x.pdf", "page": 1}]}
    monkeypatch.setattr(main, "ask", lambda q, k=4: fake)
    r = TestClient(main.app).post("/ask", json={"question": "teste"})
    assert r.status_code == 200
    assert r.json()["sources"][0]["page"] == 1


def test_endpoint_sem_pergunta_retorna_422():
    r = TestClient(main.app).post("/ask", json={})
    assert r.status_code == 422


def test_resposta_sem_contexto(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = self
            self.completions = self

        def create(self, **kwargs):
            captured.update(kwargs)

            class Msg:
                content = "Não sei com base nos documentos."

            class Choice:
                message = Msg()

            class Resp:
                choices = [Choice()]

            return Resp()

    monkeypatch.setattr(rag, "retrieve", lambda q, k=4: [])
    monkeypatch.setattr(rag, "OpenAI", FakeClient)
    monkeypatch.setenv("LLM_BASE_URL", "x")
    monkeypatch.setenv("LLM_API_KEY", "x")
    monkeypatch.setenv("LLM_MODEL", "x")

    out = rag.ask("Qual a capital da França?")
    assert "Não sei" in captured["messages"][0]["content"]
    assert out["sources"] == []