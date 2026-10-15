-- 1. Activar la extensión (la imagen ya la trae instalada, pero hay que habilitarla)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabla de chunks
CREATE TABLE IF NOT EXISTS chunks (
    id           BIGSERIAL PRIMARY KEY,
    source       TEXT        NOT NULL,           -- 'docs' o 'issue'
    doc_id       TEXT        NOT NULL,           -- ej. 'user_guide/io.rst#CSV & text files' o 'issue#51234'
    chunk_index  INT         NOT NULL,           -- posición del chunk dentro de su documento
    text         TEXT        NOT NULL,           -- el fragmento de texto
    metadata     JSONB       NOT NULL DEFAULT '{}'::jsonb,  -- url, section, label, number...
    embedding    vector(384) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (doc_id, chunk_index)                 -- permite re-indexar sin duplicar
);

-- 3. Índice vectorial HNSW con distancia coseno
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 4. Índices auxiliares para filtrar
CREATE INDEX IF NOT EXISTS chunks_source_idx   ON chunks (source);
CREATE INDEX IF NOT EXISTS chunks_metadata_gin ON chunks USING gin (metadata);