# -*- coding: utf-8 -*-
"""Planes de desarrollo y sucesión (liderazgo, desarrollo, sucesión)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.schemas import (
    AccionIn,
    EstadisticasPlanes,
    PaginaPlanes,
    PlanCreate,
    PlanDetalle,
    PlanUpdate,
)
from app.services import plan_service

router = APIRouter(prefix="/planes", tags=["Planes de desarrollo"])


class AccionMarcarRequest(BaseModel):
    completada: bool


@router.get("", response_model=PaginaPlanes, summary="Listar planes (RF-11)")
def listar(
    q: str | None = None,
    estado: str | None = None,
    area: str | None = None,
    colaborador_id: int | None = None,
    solo_abiertos: bool = False,
    pagina: int = 1,
    tamanio: int = 20,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("planes.consultar")),
):
    items, total = plan_service.listar(
        db, q=q, estado=estado, area=area, colaborador_id=colaborador_id,
        solo_abiertos=solo_abiertos, pagina=pagina, tamanio=tamanio,
    )
    return PaginaPlanes(total=total, pagina=pagina, tamanio=tamanio, items=items)


@router.get("/estadisticas", response_model=EstadisticasPlanes, summary="Resumen")
def estadisticas(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("planes.consultar")),
):
    return plan_service.estadisticas(db)


@router.post("", response_model=PlanDetalle, status_code=201, summary="Crear plan")
def crear(
    datos: PlanCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("planes.gestionar")),
):
    try:
        plan = plan_service.crear(db, user, datos)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return plan_service.obtener_detalle(db, plan.id)


@router.get("/{plan_id}", response_model=PlanDetalle, summary="Detalle del plan")
def obtener(
    plan_id: int,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("planes.consultar")),
):
    detalle = plan_service.obtener_detalle(db, plan_id)
    if detalle is None:
        raise HTTPException(404, "Plan no encontrado")
    return detalle


@router.put("/{plan_id}", response_model=PlanDetalle, summary="Actualizar plan")
def actualizar(
    plan_id: int,
    datos: PlanUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("planes.gestionar")),
):
    try:
        plan = plan_service.actualizar(db, user, plan_id, datos)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    if plan is None:
        raise HTTPException(404, "Plan no encontrado")
    return plan_service.obtener_detalle(db, plan_id)


@router.delete("/{plan_id}", status_code=204, summary="Eliminar plan")
def eliminar(
    plan_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("planes.gestionar")),
):
    if plan_service.eliminar(db, user, plan_id) is None:
        raise HTTPException(404, "Plan no encontrado")


@router.post(
    "/{plan_id}/acciones",
    status_code=201,
    summary="Agregar acción al plan",
)
def nueva_accion(
    plan_id: int,
    datos: AccionIn,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("planes.gestionar")),
):
    try:
        accion = plan_service.agregar_accion(
            db, user, plan_id, datos.descripcion, datos.fecha_limite
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    if accion is None:
        raise HTTPException(404, "Plan no encontrado")
    return {
        "id": accion.id,
        "plan_id": accion.plan_id,
        "descripcion": accion.descripcion,
        "completada": accion.completada,
        "fecha_limite": accion.fecha_limite,
    }


@router.patch(
    "/acciones/{accion_id}",
    summary="Marcar acción completada/pendiente y recalcular avance",
)
def marcar_accion(
    accion_id: int,
    datos: AccionMarcarRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("planes.gestionar")),
):
    accion, plan = plan_service.marcar_accion(db, user, accion_id, datos.completada)
    if accion is None:
        raise HTTPException(404, "Acción no encontrada")
    return {
        "accion_id": accion.id,
        "completada": accion.completada,
        "plan_id": plan.id if plan else None,
        "progreso": plan.progreso if plan else None,
        "estado": plan.estado.value if plan else None,
    }
