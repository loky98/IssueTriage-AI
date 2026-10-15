"""Búsqueda semántica sobre la tabla chunks."""
import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import CrossEncoder, SentenceTransformer

load_dotenv()

_model = None
_conn = None
_reranker = None


def get_model():
    """Carga el modelo solo la primera vez que se usa."""
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model

def get_conn():
    """Conexión perezosa; se reabre si se cerró."""
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(os.getenv("DATABASE_URL"), autocommit=True)
        register_vector(_conn)
    return _conn

def get_reranker():
    """Carga el reranker solo la primera vez que se usa."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=256)
    return _reranker
# reranker = CrossEncoder("BAAI/bge-reranker-base")
# reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=256)
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "  # recomendado por BGE para consultas

conn = psycopg.connect(os.getenv("DATABASE_URL"), autocommit=True)
register_vector(conn)

def retrieve(query, k=5, source=None, use_prefix=True):
    """Devuelve los k chunks más similares. source: None, 'docs' o 'issue'."""
    vec = get_model().encode((QUERY_PREFIX if use_prefix else "") + query, normalize_embeddings=True)
    sql = """SELECT source, text, metadata, 1 - (embedding <=> %s) AS score
            FROM chunks
            WHERE (%s::text IS NULL OR source = %s)
            ORDER BY embedding <=> %s
            LIMIT %s"""
    rows = get_conn().execute(sql, (vec, source, source, vec, k)).fetchall()
    return [{"source": s, "text": t, "metadata": m, "score": round(float(sc), 3)}
            for s, t, m, sc in rows]


def retrieve_reranked(query, k=5, candidates=20, source=None):
    """Recupera `candidates` por embeddings y los reordena con el reranker."""
    results = retrieve(query, k=candidates, source=source)
    scores = get_reranker().predict([(query, r["text"]) for r in results])
    for r, s in zip(results, scores):
        r["rerank_score"] = round(float(s), 3)
    return sorted(results, key=lambda r: r["rerank_score"], reverse=True)[:k]