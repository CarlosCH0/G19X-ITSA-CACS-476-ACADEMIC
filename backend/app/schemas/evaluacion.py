# -*- coding: utf-8 -*-
"""Esquemas de evaluación, configuración, revisiones y observaciones."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import Clasificacion, EstadoEvaluacion, EstadoRevision


# Configuracion de criterios.
class ConfiguracionCreate(BaseModel):
    """Nueva versión de criterios/ponderaciones/umbral (RF-16, RN-03)."""
    nombre: str = Field(min_length=3, max_length=120)
    pesos: dict[str, float] = Field(min_length=1)
    umbral_hipo: float = Field(ge=0, le=100)
    cobertura_minima: float = Field(default=0.8, ge=0, le=1)
    umbral_desarrollo_rel: float = Field(default=0.85, gt=0, le=1)
    activar: bool = True


class ConfiguracionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    nombre: str
    criterios: dict[str, Any]
    reglas: dict[str, Any]
    umbral_hipo: float
    activa: bool
    creado_por_id: int
    fecha_creacion: datetime


class IndicadorAreaOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    tipo: str
    activo: bool
    en_criterios: bool


class AreaPruebasOut(BaseModel):
    area: str
    indicador_ids: list[int]


class ConfiguracionAreasPruebasOut(BaseModel):
    areas: list[AreaPruebasOut]
    indicadores: list[IndicadorAreaOut]


class AreaPruebasUpdate(BaseModel):
    area: str = Field(min_length=1, max_length=120)
    indicador_ids: list[int]


# Ejecucion y resultados.
class EjecutarEvaluacionRequest(BaseModel):
    periodo: str = Field(min_length=4, max_length=20)
    colaborador_id: int | None = None
    configuracion_id: int | None = None
    generar_explicacion_ia: bool = True


class ResumenEjecucion(BaseModel):
    periodo: str
    configuracion_version: int
    version_modelo: str
    total_evaluados: int
    completos: int
    incompletos: int
    por_clasificacion: dict[str, int]
    evaluacion_ids: list[int]


class FactorOut(BaseModel):
    codigo: str
    nombre: str
    tipo: str
    peso: float
    valor: float
    normalizado: float
    contribucion: float


class RevisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoRevision
    comentario: str
    usuario_id: int
    usuario_nombre: str = ""
    fecha: datetime


class ResultadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluacion_id: int
    puntuacion: float | None
    clasificacion: Clasificacion | None
    cobertura: float
    factores: list[dict[str, Any]] | None
    explicacion: str | None
    explicacion_origen: str | None
    fecha_explicacion: datetime | None
    revisiones: list[RevisionOut] = []


class EvaluacionListado(BaseModel):
    id: int
    colaborador_id: int
    colaborador_codigo: str = ""
    colaborador_nombre: str = ""
    area: str = ""
    periodo: str
    fecha: datetime
    version_modelo: str
    estado: EstadoEvaluacion
    configuracion_version: int = 0
    puntuacion: float | None = None
    clasificacion: Clasificacion | None = None
    estado_revision: EstadoRevision | None = None


class EvaluacionDetalle(EvaluacionListado):
    resultado: ResultadoOut | None = None
    observaciones: list["ObservacionOut"] = []


# --------------------- Revisiones / observaciones ---------------------
class RevisionCreate(BaseModel):
    estado: EstadoRevision
    comentario: str = Field(default="", max_length=2000)


class ObservacionCreate(BaseModel):
    texto: str = Field(min_length=3, max_length=4000)
    colaborador_id: int | None = None


class ObservacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluacion_id: int | None
    colaborador_id: int | None
    autor_id: int
    autor_nombre: str = ""
    texto: str
    fecha: datetime


EvaluacionDetalle.model_rebuild()
