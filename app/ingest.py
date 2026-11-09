from pathlib import Path

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("data")
DB_DIR = "chroma_db"
CHUNK_SIZE = 700   # caracteres (plano: 500 a 800)
OVERLAP = 100
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    text = " ".join(text.split())
    chunks, start = [], 0
    while start < len(text):
        piece = text[start:start + size].strip()
        if piece:
            chunks.append(piece)
        start += size - overlap
    return chunks


def read_pdf(path: Path):
    reader = PdfReader(path)
    for page_num, page in enumerate(reader.pages, start=1):
        yield page_num, page.extract_text() or ""


def main():
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection("docs")
    except Exception:
        pass
    col = client.create_collection("docs", metadata={"hnsw:space": "cosine"})

    ids, docs, metas = [], [], []
    for pdf in sorted(DATA_DIR.glob("*.pdf")):
        for page_num, text in read_pdf(pdf):
            for i, chunk in enumerate(chunk_text(text)):
                ids.append(f"{pdf.stem}-p{page_num}-c{i}")
                docs.append(chunk)
                metas.append({"source": pdf.name, "page": page_num})
        print(f"Lido: {pdf.name}")

    embeddings = model.encode(docs, show_progress_bar=True).tolist()
    for i in range(0, len(ids), 500):
        col.add(
            ids=ids[i:i + 500],
            documents=docs[i:i + 500],
            embeddings=embeddings[i:i + 500],
            metadatas=metas[i:i + 500],
        )
    print(f"Pronto: {len(ids)} trechos salvos em {DB_DIR}/")


if __name__ == "__main__":
    main()