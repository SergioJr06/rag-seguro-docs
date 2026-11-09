import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_model = SentenceTransformer(MODEL_NAME)
_col = chromadb.PersistentClient(path=DB_DIR).get_collection("docs")


def retrieve(question: str, k: int = 4) -> list[dict]:
    emb = _model.encode([question]).tolist()
    r = _col.query(query_embeddings=emb, n_results=k)
    return [
        {"text": d, "source": m["source"], "page": m["page"], "distance": dist}
        for d, m, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])
    ]


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is prompt injection?"
    for hit in retrieve(q):
        print(f"[{hit['source']} p.{hit['page']}] dist={hit['distance']:.3f}")
        print(hit["text"][:200], "\n")