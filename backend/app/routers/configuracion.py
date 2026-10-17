# -*- coding: utf-8 -*-
"""Configuración de criterios de evaluación (RF-16, RN-03)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.schemas import (
    AreaPruebasUpdate,
    ConfiguracionAreasPruebasOut,
    ConfiguracionCreate,
    ConfiguracionOut,
)
from app.services import area_evaluacion_service, configuracion_service

router = APIRouter(prefix="/configuracion", tags=["Configuración de criterios"])


@router.get(
    "/areas-pruebas",
    response_model=ConfiguracionAreasPruebasOut,
    summary="Pruebas asignadas por área",
)
def listar_pruebas_por_area(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("configuracion.gestionar")),
):
    return area_evaluacion_service.listar(db)


@router.put(
    "/areas-pruebas",
    response_model=ConfiguracionAreasPruebasOut,
    summary="Actualizar pruebas de un área",
)
def actualizar_pruebas_por_area(
    datos: AreaPruebasUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("configuracion.gestionar")),
):
    try:
        return area_evaluacion_service.actualizar(db, user, datos)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.get("", response_model=list[ConfiguracionOut], summary="Versiones de criterios")
def listar(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("configuracion.gestionar")),
):
    return configuracion_service.listar(db)


@router.get("/activa", response_model=ConfiguracionOut, summary="Configuración activa")
def obtener_activa(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("configuracion.gestionar")),
):
    cfg = configuracion_service.obtener_activa(db)
    if cfg is None:
        raise HTTPException(404, "No hay configuración activa")
    return cfg


@router.post("", response_model=ConfiguracionOut, status_code=201, summary="Nueva versión (RN-03)")
def crear_version(
    datos: ConfiguracionCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("configuracion.gestionar")),
):
    try:
        return configuracion_service.crear_version(db, user, datos)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.post("/{configuracion_id}/activar", response_model=ConfiguracionOut, summary="Activar versión")
def activar(
    configuracion_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("configuracion.gestionar")),
):
    cfg = configuracion_service.activar(db, user, configuracion_id)
    if cfg is None:
        raise HTTPException(404, "Configuración no encontrada")
    return cfg
