"""Verifica la conexión a PostgreSQL y que pgvector esté activo."""
import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

load_dotenv()

with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    register_vector(conn)  # permite enviar/recibir vectores como listas o arrays de numpy
    version = conn.execute(
        "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
    ).fetchone()
    total = conn.execute("SELECT count(*) FROM chunks").fetchone()
    print(f"pgvector versión {version[0]} | filas en chunks: {total[0]}")