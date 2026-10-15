"""Agrega al índice los issues originales de los pares duplicado -> original."""
import json
import os

import psycopg
import requests
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from ingest.build_index import clean_issue, model
from ingest.fetch_issues import API, REPO, TARGET_LABELS, get

pairs = [json.loads(line) for line in open("data/raw/duplicates.jsonl", encoding="utf-8")]
eval_numbers = {json.loads(line)["number"] for line in open("evals/dataset.jsonl", encoding="utf-8")}
originals = {p["original"] for p in pairs} - eval_numbers  # nunca indexar issues de evaluación

with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    register_vector(conn)
    indexed = {r[0] for r in conn.execute("SELECT doc_id FROM chunks WHERE source = 'issue'")}
    rows = []
    for n in sorted(originals):
        if f"issue#{n}" in indexed:
            continue
        try:
            it = get(f"{API}/repos/{REPO}/issues/{n}").json()
        except requests.HTTPError:  # issue borrado o transferido
            continue
        if "pull_request" in it:  # a veces el "original" es un PR
            continue
        label = next((label_name["name"] for label_name  in it["labels"] if label_name["name"] in TARGET_LABELS), None)
        text = f"{it['title']}\n{clean_issue(it['body'] or '')}"
        rows.append((f"issue#{n}", text, {"url": it["html_url"], "number": n, "label": label}))

    vectors = model.encode([r[1] for r in rows], normalize_embeddings=True)
    conn.cursor().executemany(
        """INSERT INTO chunks (source, doc_id, chunk_index, text, metadata, embedding)
            VALUES ('issue', %s, 0, %s, %s, %s)
            ON CONFLICT (doc_id, chunk_index) DO NOTHING""",
        [(d, t, Jsonb(m), v) for (d, t, m), v in zip(rows, vectors)],
    )
print(f"{len(rows)} originales agregados al índice")