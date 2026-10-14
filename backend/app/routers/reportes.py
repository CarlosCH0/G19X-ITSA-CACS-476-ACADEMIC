# -*- coding: utf-8 -*-
"""Paneles y exportaciones (RF-12, RF-13, RF-14, RN-07). — MVP"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.services import configuracion_service, reporte_service

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/dashboard", summary="Indicadores para el panel (RF-13)")
def dashboard(
    periodo: str | None = None,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    return reporte_service.dashboard(db, periodo)


@router.get(
    "/export/evaluaciones.csv",
    response_class=PlainTextResponse,
    summary="Exportar resultados en CSV (RF-14)",
)
def exportar_evaluaciones(
    periodo: str | None = None,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.exportar")),
):
    contenido = reporte_service.exportar_evaluaciones_csv(db, periodo)
    nombre = f"evaluaciones_{periodo or 'todos'}_{datetime.now(timezone.utc):%Y%m%d}.csv"
    return PlainTextResponse(
        content=contenido,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get("/config", summary="Parámetros de clasificación vigentes")
def parametros(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    from app.core.config import settings

    cfg = configuracion_service.obtener_activa(db)
    return {
        "configuracion": {
            "version": cfg.version,
            "nombre": cfg.nombre,
            "umbral_hipo": cfg.umbral_hipo,
            "reglas": cfg.reglas,
            "pesos": cfg.criterios.get("pesos", {}),
        }
        if cfg
        else None,
        "version_modelo": settings.modelo_version,
    }
