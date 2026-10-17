# -*- coding: utf-8 -*-
"""Esquemas de planes de desarrollo y sucesión (liderazgo/desarrollo)."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import EstadoPlan


class AccionIn(BaseModel):
    descripcion: str = Field(min_length=3, max_length=255)
    fecha_limite: date | None = None
    completada: bool = False


class PlanCreate(BaseModel):
    colaborador_id: int
    titulo: str = Field(min_length=3, max_length=160)
    objetivo: str = Field(default="", max_length=2000)
    foco: str = Field(default="liderazgo", max_length=60)
    fecha_inicio: date
    fecha_fin: date
    responsable_id: int | None = None
    acciones: list[AccionIn] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validar_fechas(self) -> "PlanCreate":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        return self


class PlanUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=3, max_length=160)
    objetivo: str | None = Field(default=None, max_length=2000)
    foco: str | None = Field(default=None, max_length=60)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    responsable_id: int | None = None
    estado: EstadoPlan | None = None

    @model_validator(mode="after")
    def validar_fechas(self) -> "PlanUpdate":
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        return self


class AccionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    descripcion: str
    completada: bool
    fecha_limite: date | None
    fecha_creacion: datetime


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    colaborador_id: int
    titulo: str
    objetivo: str
    foco: str
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoPlan
    progreso: float
    responsable_id: int | None
    creado_por_id: int
    fecha_creacion: datetime
    total_acciones: int = 0
    acciones_completadas: int = 0


class PlanListado(PlanOut):
    """Listado con datos del colaborador (RF-11)."""
    colaborador_codigo: str = ""
    colaborador_nombre: str = ""
    area: str = ""
    responsable_nombre: str = ""
    en_riesgo: bool = False


class PlanDetalle(PlanOut):
    colaborador_codigo: str = ""
    colaborador_nombre: str = ""
    area: str = ""
    puesto: str = ""
    responsable_nombre: str = ""
    creado_por_nombre: str = ""
    en_riesgo: bool = False
    acciones: list[AccionOut] = []


class PaginaPlanes(BaseModel):
    total: int
    pagina: int
    tamanio: int
    items: list[PlanListado]


class EstadisticasPlanes(BaseModel):
    total: int
    por_estado: dict[str, int]
    avance_promedio: float
    en_riesgo: int
    vencidos: int
