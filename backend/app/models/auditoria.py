# -*- coding: utf-8 -*-
"""Registro de auditoría (RF-15, RNF-04)."""
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), nullable=True, index=True)
    usuario_nombre: Mapped[str] = mapped_column(String(160), default="anonimo")
    accion: Mapped[str] = mapped_column(String(80), index=True)
    recurso: Mapped[str] = mapped_column(String(160), default="")
    detalle: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
