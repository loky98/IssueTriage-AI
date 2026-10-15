"""Caché de resultados y memoria de sesión en Redis."""
import hashlib
import json
import os

import redis.asyncio as redis
from dotenv import load_dotenv

from app.schemas import TriageResult

load_dotenv()
r = redis.from_url(os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"), decode_responses=True)
TTL = 7 * 24 * 3600  # 7 días; luego Redis borra la clave solo


def _cache_key(title, body, cache_id):
    return "triage:cache:" + hashlib.sha256(f"{cache_id}\n{title}\n{body}".encode()).hexdigest()


async def get_cached(title, body, cache_id):
    raw = await r.get(_cache_key(title, body, cache_id))
    return TriageResult.model_validate_json(raw) if raw else None


async def set_cached(title, body, cache_id, result):
    await r.set(_cache_key(title, body, cache_id), result.model_dump_json(), ex=TTL)


async def add_to_session(session_id, title, result):
    key = f"triage:session:{session_id}"
    await r.rpush(key, json.dumps({"title": title, "label": result.label, "reasoning": result.reasoning}))
    await r.expire(key, TTL)


async def get_session(session_id, last=5):
    return [json.loads(x) for x in await r.lrange(f"triage:session:{session_id}", -last, -1)]