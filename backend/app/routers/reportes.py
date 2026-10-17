# -*- coding: utf-8 -*-
"""Paneles y exportaciones (RF-12, RF-13, RF-14, RN-07)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.services import reporte_service

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/dashboard", summary="Indicadores para el panel (RF-13)")
def dashboard(
    periodo: str | None = None,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    return reporte_service.dashboard(db, periodo)


@router.get("/matriz-9box", summary="Matriz de sucesión 9-box (sucesión)")
def matriz(
    periodo: str | None = None,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    """Desempeño (eje X) × potencial (eje Y) con terciles de la población."""
    return reporte_service.matriz_nueve_box(db, periodo)


@router.get("/comparar", summary="Comparar colaboradores (RF-12)")
def comparar(
    ids: str = Query(..., description="IDs separados por coma (2 a 6)"),
    periodo: str | None = None,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    try:
        lista_ids = [int(x) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(422, "Los IDs deben ser numéricos y separados por coma") from None
    if len(lista_ids) < 2:
        raise HTTPException(422, "Se requieren al menos 2 colaboradores para comparar")
    return reporte_service.comparar_colaboradores(db, lista_ids, periodo)


@router.get("/alertas", summary="Centro de alertas operativas")
def centro_alertas(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    """Pendientes de revisión, validación de datos y planes en riesgo."""
    return reporte_service.alertas(db)


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


@router.get(
    "/export/evaluaciones.xlsx",
    summary="Exportar resultados en Excel (RF-14)",
)
def exportar_evaluaciones_xlsx(
    periodo: str | None = None,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.exportar")),
):
    contenido = reporte_service.exportar_evaluaciones_xlsx(db, periodo)
    nombre = f"evaluaciones_{periodo or 'todos'}_{datetime.now(timezone.utc):%Y%m%d}.xlsx"
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get("/config", summary="Parámetros de clasificación vigentes")
def parametros(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("reportes.consultar")),
):
    from app.core.config import settings
    from app.services import configuracion_service

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
