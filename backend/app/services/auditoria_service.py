# -*- coding: utf-8 -*-
"""Servicio de auditoría (RF-15, RNF-04, RN-08).

Registra quién, cuándo y sobre qué recurso se realizó cada operación crítica.
No confirma la transacción: la confirma el caso de uso que la origina.
"""
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Auditoria


def registrar(
    db: Session,
    *,
    accion: str,
    recurso: str = "",
    usuario_id: int | None = None,
    usuario_nombre: str = "anonimo",
    detalle: dict[str, Any] | None = None,
) -> Auditoria:
    registro = Auditoria(
        accion=accion,
        recurso=recurso,
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        detalle=detalle,
    )
    db.add(registro)
    return registro


def consultar(
    db: Session,
    *,
    q: str | None = None,
    accion: str | None = None,
    pagina: int = 1,
    tamanio: int = 50,
) -> tuple[list[Auditoria], int]:
    consulta = select(Auditoria).order_by(Auditoria.fecha_hora.desc())
    if accion:
        consulta = consulta.where(Auditoria.accion == accion)
    if q:
        like = f"%{q}%"
        consulta = consulta.where(
            (Auditoria.usuario_nombre.ilike(like))
            | (Auditoria.recurso.ilike(like))
            | (Auditoria.accion.ilike(like))
        )
    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    items = list(
        db.scalars(consulta.offset((pagina - 1) * tamanio).limit(tamanio))
    )
    return items, total
