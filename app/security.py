"""Autenticación por API key y rate limit con Redis."""
import hashlib
import os
import secrets

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.memory import r

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "10"))


async def require_api_key(api_key: str | None = Security(api_key_header)) -> str:
    valid = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]
    if not api_key or not any(secrets.compare_digest(api_key, k) for k in valid):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


async def rate_limit(api_key: str = Depends(require_api_key)):
    """Ventana fija de 60 s por clave. En Redis se guarda un hash de la clave, nunca la clave."""
    key = "ratelimit:" + hashlib.sha256(api_key.encode()).hexdigest()[:16]
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, 60)
    if count > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded",
                            headers={"Retry-After": str(await r.ttl(key))})