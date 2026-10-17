# -*- coding: utf-8 -*-
"""Esquemas de colaboradores e indicadores (RF-03, RF-04, RN-01, RN-02)."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import Direccion, TipoIndicador, Validez


# ------------------------- Colaboradores -------------------------
class ColaboradorCreate(BaseModel):
    codigo: str = Field(min_length=2, max_length=30)
    nombre: str = Field(min_length=3, max_length=160)
    area: str = Field(min_length=2, max_length=120)
    puesto: str = Field(default="", max_length=120)
    fecha_ingreso: date | None = None


class ColaboradorUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=160)
    area: str | None = Field(default=None, min_length=2, max_length=120)
    puesto: str | None = Field(default=None, max_length=120)
    fecha_ingreso: date | None = None
    estado: bool | None = None


class ColaboradorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    area: str
    puesto: str
    fecha_ingreso: date | None
    estado: bool


class ColaboradorListado(ColaboradorOut):
    """Listado con datos de la última evaluación (RF-11)."""
    ultima_puntuacion: float | None = None
    ultima_clasificacion: str | None = None
    ultimo_periodo: str | None = None


class PaginaColaboradores(BaseModel):
    total: int
    pagina: int
    tamanio: int
    items: list[ColaboradorListado]


# ------------------------- Indicadores -------------------------
class IndicadorCreate(BaseModel):
    codigo: str = Field(min_length=2, max_length=60)
    nombre: str = Field(min_length=3, max_length=160)
    tipo: TipoIndicador
    direccion: Direccion = Direccion.MAYOR_MEJOR


class IndicadorUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=160)
    tipo: TipoIndicador | None = None
    direccion: Direccion | None = None
    activo: bool | None = None


class IndicadorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    tipo: TipoIndicador
    direccion: Direccion
    activo: bool


# ------------------------- Mediciones -------------------------
class MedicionIn(BaseModel):
    indicador_id: int
    valor: float
    validez: Validez = Validez.PENDIENTE
    comentario: str = ""


class MedicionBulkRequest(BaseModel):
    colaborador_id: int
    periodo: str = Field(min_length=4, max_length=20)
    mediciones: list[MedicionIn] = Field(min_length=1)


class MedicionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    colaborador_id: int
    indicador_id: int
    indicador_codigo: str = ""
    indicador_nombre: str = ""
    tipo: str = ""
    periodo: str
    valor: float
    validez: Validez
    comentario: str
    fecha_registro: datetime


class MedicionValidezUpdate(BaseModel):
    validez: Validez
    comentario: str = ""
