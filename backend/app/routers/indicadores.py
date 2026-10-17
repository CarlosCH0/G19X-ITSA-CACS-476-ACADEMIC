# -*- coding: utf-8 -*-
"""Indicadores y mediciones (RF-04, RN-01, RN-02)."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.models import Validez
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


@router.get("/plantilla-csv", response_class=PlainTextResponse, summary="Plantilla CSV")
def plantilla_csv(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("indicadores.gestionar")),
):
    contenido = indicador_service.plantilla_csv(db)
    return PlainTextResponse(
        content=contenido,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="plantilla_mediciones.csv"'},
    )


@router.get("/plantilla-xlsx", summary="Plantilla Excel con formato profesional")
def plantilla_xlsx(
    _: UserContext = Depends(require_permission("indicadores.gestionar")),
):
    contenido = indicador_service.plantilla_xlsx()
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="plantilla_mediciones.xlsx"'},
    )


class CargaCsvRequest(BaseModel):
    contenido: str = Field(min_length=10, max_length=2_000_000)
    validar_solo: bool = False


@router.post("/carga-csv", summary="Carga masiva de mediciones (validación RN-01)")
def carga_csv(
    peticion: CargaCsvRequest,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("indicadores.gestionar")),
):
    try:
        return indicador_service.cargar_mediciones_csv(
            db, user, peticion.contenido, peticion.validar_solo
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.post("/carga-xlsx", summary="Carga masiva desde Excel")
def carga_xlsx(
    archivo: UploadFile = File(...),
    validar_solo: bool = Form(False),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("indicadores.gestionar")),
):
    if not archivo.filename or not archivo.filename.lower().endswith(".xlsx"):
        raise HTTPException(422, "Selecciona un archivo Excel con extensión .xlsx.")
    contenido = archivo.file.read(10_000_001)
    if len(contenido) > 10_000_000:
        raise HTTPException(413, "El archivo Excel supera el límite de 10 MB.")
    try:
        contenido_csv = indicador_service.xlsx_a_csv(contenido)
        if len(contenido_csv.encode("utf-8")) > 2_000_000:
            raise HTTPException(413, "El contenido de la hoja supera el límite de 2 MB.")
        return indicador_service.cargar_mediciones_csv(
            db, user, contenido_csv, validar_solo
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


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
