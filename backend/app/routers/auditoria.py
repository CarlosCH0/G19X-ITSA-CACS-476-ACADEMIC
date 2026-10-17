# -*- coding: utf-8 -*-
"""Consulta del registro de auditoría (RF-15, RNF-04)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.schemas import AuditoriaOut, PaginaAuditoria
from app.services import auditoria_service

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("", response_model=PaginaAuditoria, summary="Registro de auditoría")
def consultar(
    q: str | None = None,
    accion: str | None = None,
    pagina: int = 1,
    tamanio: int = 50,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("auditoria.consultar")),
):
    items, total = auditoria_service.consultar(
        db, q=q, accion=accion, pagina=pagina, tamanio=tamanio
    )
    return PaginaAuditoria(
        total=total,
        pagina=pagina,
        tamanio=tamanio,
        items=[AuditoriaOut.model_validate(i) for i in items],
    )
