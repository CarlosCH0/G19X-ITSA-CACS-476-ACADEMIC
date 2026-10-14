# -*- coding: utf-8 -*-
"""Evaluaciones HiPo (RF-05..RF-09, RN-03..RN-05)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.schemas import (
    EjecutarEvaluacionRequest,
    EvaluacionDetalle,
    ObservacionCreate,
    ObservacionOut,
    ResumenEjecucion,
    ResultadoOut,
    RevisionOut,
)
from app.services import evaluacion_service, revision_service

router = APIRouter(prefix="/evaluaciones", tags=["Evaluaciones"])


@router.post("/ejecutar", response_model=ResumenEjecucion, summary="Ejecutar pipeline")
def ejecutar(
    peticion: EjecutarEvaluacionRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("evaluaciones.ejecutar")),
):
    try:
        return evaluacion_service.ejecutar_evaluacion(
            db,
            user,
            periodo=peticion.periodo,
            colaborador_id=peticion.colaborador_id,
            configuracion_id=peticion.configuracion_id,
        )
    except evaluacion_service.ErrorEvaluacion as e:
        raise HTTPException(422, str(e)) from e


@router.get("", summary="Listar evaluaciones (RF-11, RF-17)")
def listar(
    periodo: str | None = None,
    clasificacion: str | None = None,
    area: str | None = None,
    colaborador_id: int | None = None,
    pagina: int = 1,
    tamanio: int = 20,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    items, total = evaluacion_service.listar_evaluaciones(
        db, periodo=periodo, clasificacion=clasificacion, area=area,
        colaborador_id=colaborador_id, pagina=pagina, tamanio=tamanio,
    )
    return {"total": total, "pagina": pagina, "tamanio": tamanio, "items": items}


@router.get("/{evaluacion_id}", response_model=EvaluacionDetalle, summary="Detalle (RF-09)")
def detalle(
    evaluacion_id: int,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    ev = evaluacion_service.obtener_detalle(db, evaluacion_id)
    if ev is None:
        raise HTTPException(404, "Evaluación no encontrada")
    res = ev.resultado
    resultado = None
    if res:
        resultado = ResultadoOut(
            id=res.id,
            evaluacion_id=res.evaluacion_id,
            puntuacion=res.puntuacion,
            clasificacion=res.clasificacion,
            cobertura=res.cobertura,
            factores=res.factores,
            explicacion=res.explicacion,
            explicacion_origen=res.explicacion_origen,
            fecha_explicacion=res.fecha_explicacion,
            revisiones=[
                RevisionOut(
                    id=r.id, estado=r.estado, comentario=r.comentario,
                    usuario_id=r.usuario_id,
                    usuario_nombre=r.usuario.nombre if r.usuario else "",
                    fecha=r.fecha,
                )
                for r in res.revisiones
            ],
        )
    observaciones = [
        ObservacionOut(
            id=o.id, evaluacion_id=o.evaluacion_id, colaborador_id=o.colaborador_id,
            autor_id=o.autor_id, autor_nombre=o.autor.nombre if o.autor else "",
            texto=o.texto, fecha=o.fecha,
        )
        for o in ev.observaciones
    ]
    return EvaluacionDetalle(
        id=ev.id,
        colaborador_id=ev.colaborador_id,
        colaborador_codigo=ev.colaborador.codigo,
        colaborador_nombre=ev.colaborador.nombre,
        area=ev.colaborador.area,
        periodo=ev.periodo,
        fecha=ev.fecha,
        version_modelo=ev.version_modelo,
        estado=ev.estado,
        configuracion_version=ev.configuracion.version if ev.configuracion else 0,
        puntuacion=res.puntuacion if res else None,
        clasificacion=res.clasificacion if res else None,
        estado_revision=evaluacion_service._estado_revision_de(res),
        resultado=resultado,
        observaciones=observaciones,
    )


@router.post(
    "/{evaluacion_id}/observaciones",
    response_model=ObservacionOut,
    status_code=201,
    summary="Agregar observación (RF-19)",
)
def agregar_observacion(
    evaluacion_id: int,
    datos: ObservacionCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("evaluaciones.revisar")),
):
    try:
        obs = revision_service.agregar_observacion(db, user, evaluacion_id, datos)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    if obs is None:
        raise HTTPException(404, "Evaluación no encontrada")
    return ObservacionOut(
        id=obs.id, evaluacion_id=obs.evaluacion_id, colaborador_id=obs.colaborador_id,
        autor_id=obs.autor_id, autor_nombre=user.nombre, texto=obs.texto, fecha=obs.fecha,
    )
