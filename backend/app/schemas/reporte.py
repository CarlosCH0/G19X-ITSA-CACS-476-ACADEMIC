# -*- coding: utf-8 -*-
"""Esquemas de reportes, auditoría e IA asistida (RF-08, RF-12..RF-15)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


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
