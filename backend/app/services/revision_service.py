# -*- coding: utf-8 -*-
"""Revisión humana de resultados y observaciones (RF-18, RF-19, RN-06)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import UserContext
from app.models import (
    Colaborador,
    Evaluacion,
    Observacion,
    ResultadoEvaluacion,
    RevisionHumana,
)
from app.schemas import ObservacionCreate, RevisionCreate
from app.services import auditoria_service


def registrar_revision(
    db: Session, usuario: UserContext, resultado_id: int, datos: RevisionCreate
) -> RevisionHumana | None:
    resultado = db.get(ResultadoEvaluacion, resultado_id)
    if resultado is None:
        return None
    revision = RevisionHumana(
        resultado_id=resultado_id,
        usuario_id=usuario.id,
        estado=datos.estado,
        comentario=datos.comentario,
    )
    db.add(revision)
    auditoria_service.registrar(
        db, accion="revision.humana", recurso=f"resultado:{resultado_id}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={"estado": datos.estado.value},
    )
    db.commit()
    db.refresh(revision)
    return revision


def agregar_observacion(
    db: Session, usuario: UserContext, evaluacion_id: int, datos: ObservacionCreate
) -> Observacion | None:
    evaluacion = db.get(Evaluacion, evaluacion_id)
    if evaluacion is None:
        return None
    colaborador_id = datos.colaborador_id or evaluacion.colaborador_id
    if db.get(Colaborador, colaborador_id) is None:
        raise ValueError("Colaborador inexistente")
    obs = Observacion(
        evaluacion_id=evaluacion_id,
        colaborador_id=colaborador_id,
        autor_id=usuario.id,
        texto=datos.texto,
    )
    db.add(obs)
    auditoria_service.registrar(
        db, accion="observacion.crear", recurso=f"evaluacion:{evaluacion_id}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
    )
    db.commit()
    db.refresh(obs)
    return obs


def observaciones_de_colaborador(db: Session, colaborador_id: int) -> list[Observacion]:
    return list(
        db.scalars(
            select(Observacion)
            .where(Observacion.colaborador_id == colaborador_id)
            .order_by(Observacion.fecha.desc())
        )
    )
