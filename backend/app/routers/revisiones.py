# -*- coding: utf-8 -*-
"""Revisión humana de resultados (RF-18, RN-06)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.schemas import RevisionCreate, RevisionOut
from app.services import revision_service

router = APIRouter(prefix="/revisiones", tags=["Revisión humana"])


@router.post(
    "/resultados/{resultado_id}",
    response_model=RevisionOut,
    status_code=201,
    summary="Revisar/confirmar/marcar pendiente (RF-18)",
)
def registrar_revision(
    resultado_id: int,
    datos: RevisionCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("evaluaciones.revisar")),
):
    revision = revision_service.registrar_revision(db, user, resultado_id, datos)
    if revision is None:
        raise HTTPException(404, "Resultado no encontrado")
    return RevisionOut(
        id=revision.id, estado=revision.estado, comentario=revision.comentario,
        usuario_id=revision.usuario_id, usuario_nombre=user.nombre, fecha=revision.fecha,
    )
