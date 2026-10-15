import os
import time

import psycopg
from pgvector.psycopg import register_vector

from app.rag import QUERY_PREFIX, model

t = time.time()
vec = model.encode(QUERY_PREFIX + "read_csv semicolon separator", normalize_embeddings=True)
print(f"encode:  {time.time() - t:.1f}s")

t = time.time()
conn = psycopg.connect(os.getenv("DATABASE_URL"))
print(f"connect: {time.time() - t:.1f}s")

register_vector(conn)
t = time.time()
conn.execute("SELECT id FROM chunks ORDER BY embedding <=> %s LIMIT 6", (vec,)).fetchall()
print(f"query:   {time.time() - t:.1f}s")