# -*- coding: utf-8 -*-
"""Esquemas de reportes, auditoría e IA asistida (RF-08, RF-12..RF-15)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int | None
    usuario_nombre: str
    accion: str
    recurso: str
    detalle: dict[str, Any] | None
    fecha_hora: datetime


class PaginaAuditoria(BaseModel):
    total: int
    pagina: int
    tamanio: int
    items: list[AuditoriaOut]


class ConsultaAsistidaRequest(BaseModel):
    """Consulta asistida por IA usando solo contexto autorizado (RF-08)."""
    pregunta: str = Field(min_length=5, max_length=1000)
    colaborador_id: int | None = None
    periodo: str | None = Field(default=None, max_length=20)


class ConsultaAsistidaResponse(BaseModel):
    respuesta: str
    origen: str
    advertencia: str | None = None
