# -*- coding: utf-8 -*-
"""Dependencias de autenticación y autorización (RF-01, RF-02, RNF-02)."""
from dataclasses import dataclass, field

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.base import get_db
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login", auto_error=False)


@dataclass
class UserContext:
    """Contexto del usuario autenticado para la petición en curso."""
    id: int
    nombre: str
    correo: str
    rol: str
    permisos: set[str] = field(default_factory=set)

    def puede(self, codigo_permiso: str) -> bool:
        return codigo_permiso in self.permisos


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserContext:
    """Resuelve el usuario del token.

    Los permisos SIEMPRE se leen frescos desde la BD (no del token), así un
    cambio de rol aplica de inmediato sin esperar a que expire la sesión.
    """
    credenciales = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido/expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credenciales
    try:
        payload = decode_token(token)
        usuario_id = int(payload.get("sub", "0"))
    except (jwt.PyJWTError, ValueError):
        raise credenciales from None

    usuario = db.get(models.Usuario, usuario_id)
    if usuario is None or not usuario.estado:
        raise credenciales

    return UserContext(
        id=usuario.id,
        nombre=usuario.nombre,
        correo=usuario.correo,
        rol=usuario.rol.nombre if usuario.rol else "",
        permisos={p.codigo for p in usuario.rol.permisos} if usuario.rol else set(),
    )


def require_permission(codigo_permiso: str):
    """Fábrica de dependencia: exige un permiso concreto (RBAC)."""

    def verificador(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.puede(codigo_permiso):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere el permiso '{codigo_permiso}'",
            )
        return user

    return verificador
