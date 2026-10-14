# -*- coding: utf-8 -*-
"""Operación analítica: configuración de criterios, evaluaciones, resultados,
revisión humana y observaciones (RF-05..RF-09, RF-16..RF-19, RN-03..RN-06)."""
import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime, Enum, Float, ForeignKey, JSON, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EstadoEvaluacion(str, enum.Enum):
    COMPLETA = "completa"
    INCOMPLETA = "incompleta"


class Clasificacion(str, enum.Enum):
    ALTO_POTENCIAL = "alto_potencial"
    EN_DESARROLLO = "en_desarrollo"
    ESTANDAR = "estandar"
    NO_EVALUABLE = "no_evaluable"


class EstadoRevision(str, enum.Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"


class ConfiguracionEvaluacion(Base):
    """Versión de criterios, ponderaciones y umbral HiPo (RF-16, RN-03)."""
    __tablename__ = "configuracion_evaluacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    # {"pesos": {"CODIGO_INDICADOR": 0.25, ...}}
    criterios: Mapped[dict[str, Any]] = mapped_column(JSON)
    # {"cobertura_minima": 0.8, "umbral_desarrollo_rel": 0.85, "min_mediciones_validas": 1}
    reglas: Mapped[dict[str, Any]] = mapped_column(JSON)
    umbral_hipo: Mapped[float] = mapped_column(Float)
    activa: Mapped[bool] = mapped_column(default=False, index=True)
    creado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    creado_por: Mapped["Usuario"] = relationship(lazy="selectin")  # noqa: F821
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(back_populates="configuracion")


class Evaluacion(Base):
    """Ejecución del flujo para un colaborador en un periodo (RN-04, RN-05)."""
    __tablename__ = "evaluacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    colaborador_id: Mapped[int] = mapped_column(ForeignKey("colaborador.id"), index=True)
    configuracion_id: Mapped[int] = mapped_column(
        ForeignKey("configuracion_evaluacion.id"), index=True
    )
    periodo: Mapped[str] = mapped_column(String(20), index=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    version_modelo: Mapped[str] = mapped_column(String(40))
    estado: Mapped[EstadoEvaluacion] = mapped_column(
        Enum(EstadoEvaluacion, native_enum=False, length=15),
        default=EstadoEvaluacion.COMPLETA,
    )
    ejecutado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))

    colaborador: Mapped["Colaborador"] = relationship(  # noqa: F821
        back_populates="evaluaciones", lazy="selectin"
    )
    configuracion: Mapped["ConfiguracionEvaluacion"] = relationship(
        back_populates="evaluaciones", lazy="selectin"
    )
    resultado: Mapped["ResultadoEvaluacion | None"] = relationship(
        back_populates="evaluacion", uselist=False, cascade="all, delete-orphan"
    )
    observaciones: Mapped[list["Observacion"]] = relationship(back_populates="evaluacion")


class ResultadoEvaluacion(Base):
    """Puntuación, clasificación y factores principales (RF-09, trazabilidad)."""
    __tablename__ = "resultado_evaluacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluacion_id: Mapped[int] = mapped_column(
        ForeignKey("evaluacion.id"), unique=True, index=True
    )
    puntuacion: Mapped[float | None] = mapped_column(Float, nullable=True)
    clasificacion: Mapped[Clasificacion | None] = mapped_column(
        Enum(Clasificacion, native_enum=False, length=25), nullable=True
    )
    cobertura: Mapped[float] = mapped_column(Float, default=0.0)
    # [{codigo, nombre, tipo, peso, valor, normalizado, contribucion}, ...]
    factores: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    explicacion_origen: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fecha_explicacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    evaluacion: Mapped["Evaluacion"] = relationship(back_populates="resultado")
    revisiones: Mapped[list["RevisionHumana"]] = relationship(
        back_populates="resultado", cascade="all, delete-orphan", lazy="selectin"
    )


class RevisionHumana(Base):
    """Revisión humana de un resultado (RF-18, RN-06)."""
    __tablename__ = "revision_humana"

    id: Mapped[int] = mapped_column(primary_key=True)
    resultado_id: Mapped[int] = mapped_column(
        ForeignKey("resultado_evaluacion.id"), index=True
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), index=True)
    estado: Mapped[EstadoRevision] = mapped_column(
        Enum(EstadoRevision, native_enum=False, length=15)
    )
    comentario: Mapped[str] = mapped_column(Text, default="")
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    resultado: Mapped["ResultadoEvaluacion"] = relationship(back_populates="revisiones")
    usuario: Mapped["Usuario"] = relationship(lazy="selectin")  # noqa: F821


class Observacion(Base):
    """Comentarios asociados a una evaluación o colaborador (RF-19)."""
    __tablename__ = "observacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluacion.id"), nullable=True, index=True
    )
    colaborador_id: Mapped[int | None] = mapped_column(
        ForeignKey("colaborador.id"), nullable=True, index=True
    )
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), index=True)
    texto: Mapped[str] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evaluacion: Mapped["Evaluacion | None"] = relationship(back_populates="observaciones")
    colaborador: Mapped["Colaborador | None"] = relationship(  # noqa: F821
        back_populates="observaciones"
    )
    autor: Mapped["Usuario"] = relationship(lazy="selectin")  # noqa: F821
