"""recall@5 del retrieval, con y sin reranker, usando pares de duplicados."""
import json
import os
from datetime import date
from pathlib import Path

import psycopg

from app.rag import get_reranker, retrieve, retrieve_reranked
from ingest.build_index import clean_issue

pairs = [json.loads(line) for line in open("data/raw/duplicates.jsonl", encoding="utf-8")]

# solo sirven los pares cuyo original está indexado
with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    indexed = {r[0] for r in conn.execute("SELECT doc_id FROM chunks WHERE source = 'issue'")}
pairs = [p for p in pairs if f"issue#{p['original']}" in indexed]


def hit(results, pair):
    # excluye el propio duplicado si también está indexado
    numbers = [r["metadata"].get("number") for r in results if r["metadata"].get("number") != pair["number"]]
    return pair["original"] in numbers[:5]


base = rerank = 0
for p in pairs:
    query = f"{p['title']}\n{clean_issue(p['body'])}"
    base += hit(retrieve(query, k=6, source="issue"), p)
    rerank += hit(retrieve_reranked(query, k=6, candidates=20, source="issue"), p)

n = len(pairs)
report = (f"# Retrieval eval {date.today()}\n\nPares evaluados: {n}\n\n"
        f"- recall@5 sin reranker: {base / n:.2%}\n- recall@5 con reranker: {rerank / n:.2%}\n")
Path("evals/results").mkdir(parents=True, exist_ok=True)
Path(f"evals/results/retrieval_{date.today()}.md").write_text(report, encoding="utf-8")
print(report)



def rerank_titles(title, results, k=6):
    scores = get_reranker().predict([(title, r["text"].split("\n")[0]) for r in results])
    return [r for _, r in sorted(zip(scores, results), key=lambda x: x[0], reverse=True)][:k]


base = no_prefix = titles = 0
for i, p in enumerate(pairs, 1):
    query = f"{p['title']}\n{clean_issue(p['body'])}"
    base += hit(retrieve(query, k=6, source="issue"), p)
    no_prefix += hit(retrieve(query, k=6, source="issue", use_prefix=False), p)
    titles += hit(rerank_titles(p["title"], retrieve(query, k=20, source="issue", use_prefix=False)), p)
    print(f"{i}/{len(pairs)}", flush=True)

n = len(pairs)
print(f"con prefijo: {base/n:.2%} | sin prefijo: {no_prefix/n:.2%} | rerank títulos: {titles/n:.2%}")