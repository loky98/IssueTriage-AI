"""Divide docs e issues en chunks, calcula embeddings y los guarda en pgvector."""
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split

load_dotenv()
model = SentenceTransformer("BAAI/bge-small-en-v1.5")  # 384 dimensiones
splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)  # en caracteres


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def clean_issue(body):
    body = body.split("### Installed Versions")[0]  # quita el bloque de versiones
    lines = [line for line in body.splitlines() if not line.strip().startswith("- [")]  # quita checkboxes
    return "\n".join(lines).strip()[:1000]


def build_rows():
    rows = []
    for d in read_jsonl("data/processed/docs.jsonl"):
        doc_id = f"{d['source']}#{d['section']}"
        for i, chunk in enumerate(splitter.split_text(d["text"])):
            meta = {"url": d["url"], "section": d["section"], "file": d["source"]}
            rows.append(("docs", doc_id, i, f"{d['section']}\n{chunk}", meta))

    issues = read_jsonl("data/raw/issues.jsonl")
    train, evalset = train_test_split(
        issues, test_size=200, stratify=[i["label"] for i in issues], random_state=42
    )
    Path("evals").mkdir(exist_ok=True)
    with open("evals/dataset.jsonl", "w", encoding="utf-8") as f:  # nunca se indexa
        for it in evalset:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    for it in train:
        meta = {"url": it["url"], "number": it["number"], "label": it["label"]}
        text = f"{it['title']}\n{clean_issue(it['body'])}"
        rows.append(("issue", f"issue#{it['number']}", 0, text, meta))
    return rows


def main():
    rows = build_rows()
    vectors = model.encode([r[3] for r in rows], batch_size=64,
                        normalize_embeddings=True, show_progress_bar=True)
    with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO chunks (source, doc_id, chunk_index, text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id, chunk_index) DO UPDATE
                SET text = EXCLUDED.text, metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding
                """,
                [(s, d, i, t, Jsonb(m), v) for (s, d, i, t, m), v in zip(rows, vectors)],
            )
    print(f"{len(rows)} chunks indexados")


if __name__ == "__main__":
    main()