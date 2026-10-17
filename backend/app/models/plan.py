# -*- coding: utf-8 -*-
"""Planes de desarrollo y sucesión (objetivo de negocio: liderazgo y sucesión).

Un plan agrupa acciones de desarrollo para un colaborador (típicamente HiPo),
con responsable, horizonte temporal, avance y trazabilidad de auditoría.
"""
import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EstadoPlan(str, enum.Enum):
    PLANIFICADO = "planificado"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"

    @property
    def es_cerrable(self) -> bool:
        return self in (EstadoPlan.COMPLETADO, EstadoPlan.CANCELADO)


class PlanDesarrollo(Base):
    """Plan de desarrollo individual para sucesión/liderazgo."""
    __tablename__ = "plan_desarrollo"

    id: Mapped[int] = mapped_column(primary_key=True)
    colaborador_id: Mapped[int] = mapped_column(
        ForeignKey("colaborador.id"), index=True
    )
    titulo: Mapped[str] = mapped_column(String(160))
    objetivo: Mapped[str] = mapped_column(Text, default="")
    # Rol sucesorio al que se prepara: liderazgo, especialista, etc.
    foco: Mapped[str] = mapped_column(String(60), default="liderazgo")
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    estado: Mapped[EstadoPlan] = mapped_column(
        Enum(EstadoPlan, native_enum=False, length=15),
        default=EstadoPlan.PLANIFICADO, index=True,
    )
    progreso: Mapped[float] = mapped_column(Float, default=0.0)
    responsable_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id"), nullable=True
    )
    creado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_actualizacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    colaborador: Mapped["Colaborador"] = relationship(lazy="selectin")  # noqa: F821
    responsable: Mapped["Usuario | None"] = relationship(  # noqa: F821
        foreign_keys=[responsable_id], lazy="selectin"
    )
    creado_por: Mapped["Usuario"] = relationship(  # noqa: F821
        foreign_keys=[creado_por_id], lazy="selectin"
    )
    acciones: Mapped[list["AccionPlan"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", lazy="selectin"
    )


class AccionPlan(Base):
    """Acción concreta dentro de un plan (capacitación, mentoría, reto…)."""
    __tablename__ = "accion_plan"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plan_desarrollo.id"), index=True
    )
    descripcion: Mapped[str] = mapped_column(String(255))
    completada: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_limite: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    plan: Mapped["PlanDesarrollo"] = relationship(back_populates="acciones")
