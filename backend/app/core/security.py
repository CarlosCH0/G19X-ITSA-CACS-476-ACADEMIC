# -*- coding: utf-8 -*-
"""Seguridad de autenticación (RNF-01).

- Contraseñas: hash PBKDF2-SHA256 con sal aleatoria (nunca texto plano).
- Tokens: JWT firmados (HS256) con expiración.
"""
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings

ALGORITMO_HASH = "pbkdf2_sha256"
ITERACIONES = 390_000  # OWASP 2023 recomienda >= 600k para PBKDF2-SHA256 en FIPS; ajustable
# Se usa un valor alto y configurable por entorno sin dependencias nativas.


def hash_password(texto_plano: str) -> str:
    """Genera el hash de una contraseña con sal aleatoria."""
    sal = secrets.token_hex(16)
    derivado = hashlib.pbkdf2_hmac("sha256", texto_plano.encode("utf-8"), sal.encode("utf-8"), ITERACIONES)
    return f"{ALGORITMO_HASH}${ITERACIONES}${sal}${derivado.hex()}"


def verify_password(texto_plano: str, hash_almacenado: str) -> bool:
    """Verifica una contraseña contra su hash almacenado (comparación constante)."""
    try:
        algoritmo, iteraciones, sal, hash_hex = hash_almacenado.split("$")
        if algoritmo != ALGORITMO_HASH:
            return False
        derivado = hashlib.pbkdf2_hmac(
            "sha256", texto_plano.encode("utf-8"), sal.encode("utf-8"), int(iteraciones)
        )
        return hmac.compare_digest(derivado.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def create_access_token(usuario_id: int, rol: str, permisos: list[str]) -> str:
    """Emite un JWT con subject, rol, permisos, jti y expiración."""
    ahora = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "rol": rol,
        "permisos": permisos,
        "iat": ahora,
        "jti": uuid.uuid4().hex,
        "exp": ahora + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algoritmo_token)


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un JWT. Lanza jwt.PyJWTError si es inválido/expirado."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algoritmo_token])
