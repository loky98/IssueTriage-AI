Resultados

Con reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=256)
Pares evaluados: 167

- recall@5 sin reranker: 76.65%
- recall@5 con reranker: 51.50%

Con reranker = CrossEncoder("BAAI/bge-reranker-base")
Pares evaluados: 167

- recall@5 sin reranker: 76.65%
- recall@5 con reranker: 41.32%