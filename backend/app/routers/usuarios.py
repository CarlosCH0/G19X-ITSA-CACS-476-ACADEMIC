# -*- coding: utf-8 -*-
"""Gestión de usuarios, roles y permisos (RF-02, RNF-02)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.core.security import hash_password
from app.db.base import get_db
from app.models import Rol, Usuario
from app.schemas import (
    PaginaUsuarios,
    RolOut,
    UsuarioCreate,
    UsuarioOut,
    UsuarioUpdate,
)
from app.services import auditoria_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios y roles"])


@router.get("", response_model=PaginaUsuarios, summary="Listar usuarios")
def listar_usuarios(
    pagina: int = 1,
    tamanio: int = 20,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("usuarios.gestionar")),
):
    consulta = select(Usuario)
    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    usuarios = db.scalars(
        consulta.order_by(Usuario.nombre).offset((pagina - 1) * tamanio).limit(tamanio)
    ).all()
    return PaginaUsuarios(
        total=total, pagina=pagina, tamanio=tamanio, items=[UsuarioOut.model_validate(u) for u in usuarios]
    )


@router.get("/roles", response_model=list[RolOut], summary="Roles y permisos")
def listar_roles(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("usuarios.gestionar")),
):
    return db.scalars(select(Rol).order_by(Rol.id)).all()


@router.post("", response_model=UsuarioOut, status_code=201, summary="Crear usuario")
def crear_usuario(
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("usuarios.gestionar")),
):
    if db.scalars(select(Usuario).where(Usuario.correo == datos.correo)).first():
        raise HTTPException(409, f"Ya existe un usuario con el correo {datos.correo}")
    if db.get(Rol, datos.rol_id) is None:
        raise HTTPException(422, "Rol inexistente")
    usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo,
        password_hash=hash_password(datos.password),
        rol_id=datos.rol_id,
    )
    db.add(usuario)
    db.flush()
    auditoria_service.registrar(
        db, accion="usuario.crear", recurso=usuario.correo,
        usuario_id=user.id, usuario_nombre=user.nombre,
        detalle={"correo": usuario.correo, "rol_id": usuario.rol_id},
    )
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioOut, summary="Actualizar usuario")
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("usuarios.gestionar")),
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(404, "Usuario no encontrado")
    cambios = datos.model_dump(exclude_unset=True)
    if "password" in cambios:
        usuario.password_hash = hash_password(cambios.pop("password"))
    if "rol_id" in cambios and db.get(Rol, cambios["rol_id"]) is None:
        raise HTTPException(422, "Rol inexistente")
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    auditoria_service.registrar(
        db, accion="usuario.actualizar", recurso=usuario.correo,
        usuario_id=user.id, usuario_nombre=user.nombre,
        detalle={k: v for k, v in datos.model_dump(exclude_unset=True).items() if k != "password"},
    )
    db.commit()
    db.refresh(usuario)
    return usuario
