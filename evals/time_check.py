import time

from app.rag import retrieve, retrieve_reranked

t = time.time()
retrieve("read_csv semicolon separator", k=6, source="issue")
print(f"retrieve: {time.time() - t:.1f}s")
t = time.time()
retrieve_reranked("read_csv semicolon separator", k=6, candidates=20, source="issue")
print(f"rerank:   {time.time() - t:.1f}s")