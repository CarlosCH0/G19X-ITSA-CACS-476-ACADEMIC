# -*- coding: utf-8 -*-
"""Autenticación (RF-01, RNF-01)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import UserContext, get_current_user
from app.core.security import create_access_token, verify_password
from app.db.base import get_db
from app.models import Usuario
from app.schemas import LoginRequest, TokenResponse, UsuarioMe
from app.services import auditoria_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.scalars(select(Usuario).where(Usuario.correo == datos.correo)).first()
    if (
        usuario is None
        or not usuario.estado
        or not verify_password(datos.password, usuario.password_hash)
    ):
        auditoria_service.registrar(
            db, accion="auth.login_fallido", recurso=str(datos.correo)
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

    permisos = [p.codigo for p in usuario.rol.permisos] if usuario.rol else []
    token = create_access_token(usuario.id, usuario.rol.nombre if usuario.rol else "", permisos)
    auditoria_service.registrar(
        db,
        accion="auth.login",
        recurso=usuario.correo,
        usuario_id=usuario.id,
        usuario_nombre=usuario.nombre,
    )
    db.commit()
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
        usuario=UsuarioMe(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            rol=usuario.rol.nombre if usuario.rol else "",
            permisos=permisos,
        ),
    )


@router.get("/me", response_model=UsuarioMe, summary="Usuario autenticado")
def quien_soy(user: UserContext = Depends(get_current_user)):
    return UsuarioMe(
        id=user.id, nombre=user.nombre, correo=user.correo, rol=user.rol,
        permisos=sorted(user.permisos),
    )
