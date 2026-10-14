# -*- coding: utf-8 -*-
"""Indicadores y mediciones (RF-04, RN-01, RN-02). — MVP"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.schemas import (
    IndicadorCreate,
    IndicadorOut,
    IndicadorUpdate,
    MedicionBulkRequest,
    MedicionOut,
    MedicionValidezUpdate,
)
from app.services import indicador_service

router = APIRouter(prefix="/indicadores", tags=["Indicadores y mediciones"])


@router.get("", response_model=list[IndicadorOut], summary="Catálogo de indicadores")
def listar(
    solo_activos: bool = False,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("colaboradores.consultar")),
):
    return indicador_service.listar_indicadores(db, solo_activos)


@router.post("", response_model=IndicadorOut, status_code=201, summary="Crear indicador")
def crear(
    datos: IndicadorCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("indicadores.gestionar")),
):
    try:
        return indicador_service.crear_indicador(db, user, datos)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e


@router.put("/{indicador_id}", response_model=IndicadorOut, summary="Actualizar indicador")
def actualizar(
    indicador_id: int,
    datos: IndicadorUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("indicadores.gestionar")),
):
    ind = indicador_service.actualizar_indicador(db, user, indicador_id, datos)
    if ind is None:
        raise HTTPException(404, "Indicador no encontrado")
    return ind


@router.get("/periodos", summary="Periodos con mediciones")
def periodos(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("colaboradores.consultar")),
):
    return indicador_service.periodos_disponibles(db)


@router.get("/mediciones", summary="Mediciones de un colaborador")
def mediciones(
    colaborador_id: int,
    periodo: str | None = None,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("colaboradores.consultar")),
):
    filas = indicador_service.mediciones_de_colaborador(db, colaborador_id, periodo)
    return [
        MedicionOut(
            id=m.id,
            colaborador_id=m.colaborador_id,
            indicador_id=m.indicador_id,
            indicador_codigo=m.indicador.codigo,
            indicador_nombre=m.indicador.nombre,
            tipo=m.indicador.tipo.value,
            periodo=m.periodo,
            valor=m.valor,
            validez=m.validez,
            comentario=m.comentario,
            fecha_registro=m.fecha_registro,
        )
        for m in filas
    ]


@router.post("/mediciones", status_code=201, summary="Cargar mediciones (bulk)")
def cargar_mediciones(
    peticion: MedicionBulkRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("indicadores.gestionar")),
):
    try:
        indicador_service.registrar_mediciones(db, user, peticion)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return {"detalle": "Mediciones registradas", "cantidad": len(peticion.mediciones)}


@router.patch("/mediciones/{medicion_id}/validez", summary="Validar medición (RN-01)")
def cambiar_validez(
    medicion_id: int,
    datos: MedicionValidezUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("indicadores.gestionar")),
):
    m = indicador_service.cambiar_validez(db, user, medicion_id, datos.validez, datos.comentario)
    if m is None:
        raise HTTPException(404, "Medición no encontrada")
    return {"detalle": f"Validez actualizada a {m.validez.value}"}
