# ---------- base común ----------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home appuser
WORKDIR /app

# ---------- dependencias del servidor MCP ----------
FROM base AS mcp-deps
COPY requirements-mcp.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements-mcp.txt

# ---------- imagen final: servidor MCP ----------
FROM base AS mcp
COPY --from=mcp-deps /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY ingest/__init__.py ingest/fetch_issues.py ingest/
COPY mcp_server/ mcp_server/
USER appuser
CMD ["python", "-m", "mcp_server.server"]

# ---------- dependencias de la API (torch CPU + modelos) ----------
FROM base AS api-deps
COPY requirements-api.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements-api.txt
ENV HF_HOME=/opt/hf
RUN /opt/venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# ---------- imagen final: API ----------
FROM base AS api
COPY --from=api-deps /opt/venv /opt/venv
COPY --from=api-deps /opt/hf /opt/hf
ENV PATH=/opt/venv/bin:$PATH HF_HOME=/opt/hf HF_HUB_OFFLINE=1
COPY app/ app/
COPY ingest/ ingest/
COPY mcp_server/ mcp_server/
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]