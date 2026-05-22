from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Header
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None


async def require_api_key(x_api_key: str | None = Header(None)) -> None:
    """Verifica el header X-API-Key para acceso a Copilot Studio y otros agentes externos.

    Si GRANTFLOW_API_KEY no está configurada, permite acceso libre (dev).
    Si está configurada, requiere que coincida exactamente.
    """
    if not settings.GRANTFLOW_API_KEY:
        return  # Sin autenticación en desarrollo

    if not x_api_key or x_api_key != settings.GRANTFLOW_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
