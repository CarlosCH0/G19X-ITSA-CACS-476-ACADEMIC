# -*- coding: utf-8 -*-
"""Catálogo de indicadores y mediciones por periodo (RF-04, RN-01, RN-02)."""
import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


area_indicador = Table(
    "area_indicador",
    Base.metadata,
    Column("area_evaluacion_id", ForeignKey("area_evaluacion.id", ondelete="CASCADE"), primary_key=True),
    Column("indicador_id", ForeignKey("indicador.id", ondelete="CASCADE"), primary_key=True),
)


class TipoIndicador(str, enum.Enum):
    DESEMPENO = "desempeno"
    COMPETENCIA = "competencia"
    CAPACITACION = "capacitacion"
    EXPERIENCIA = "experiencia"
    OBJETIVO = "objetivo"
    ORGANIZACIONAL = "organizacional"


class Direccion(str, enum.Enum):
    """Sentido en el que un mayor valor es mejor o peor."""
    MAYOR_MEJOR = "mayor_mejor"
    MENOR_MEJOR = "menor_mejor"


class Validez(str, enum.Enum):
    """Estado de validez de una medición (RN-01 / RN-02)."""
    VALIDA = "valida"
    PENDIENTE = "pendiente"
    INVALIDA = "invalida"


class Indicador(Base):
    __tablename__ = "indicador"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    tipo: Mapped[TipoIndicador] = mapped_column(
        Enum(TipoIndicador, native_enum=False, length=30), index=True
    )
    direccion: Mapped[Direccion] = mapped_column(
        Enum(Direccion, native_enum=False, length=20), default=Direccion.MAYOR_MEJOR
    )
    activo: Mapped[bool] = mapped_column(default=True)

    mediciones: Mapped[list["MedicionIndicador"]] = relationship(
        back_populates="indicador", cascade="all, delete-orphan"
    )
    areas_evaluacion: Mapped[list["AreaEvaluacion"]] = relationship(
        secondary=area_indicador, back_populates="indicadores"
    )


class AreaEvaluacion(Base):
    __tablename__ = "area_evaluacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    area: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    indicadores: Mapped[list[Indicador]] = relationship(
        secondary=area_indicador, back_populates="areas_evaluacion", lazy="selectin"
    )


class MedicionIndicador(Base):
    __tablename__ = "medicion_indicador"
    __table_args__ = (
        UniqueConstraint(
            "colaborador_id", "indicador_id", "periodo", name="uq_medicion_periodo"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    colaborador_id: Mapped[int] = mapped_column(
        ForeignKey("colaborador.id"), index=True
    )
    indicador_id: Mapped[int] = mapped_column(
        ForeignKey("indicador.id"), index=True
    )
    periodo: Mapped[str] = mapped_column(String(20), index=True)
    valor: Mapped[float] = mapped_column(Float)
    validez: Mapped[Validez] = mapped_column(
        Enum(Validez, native_enum=False, length=15), default=Validez.PENDIENTE, index=True
    )
    comentario: Mapped[str] = mapped_column(String(255), default="")
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    colaborador: Mapped["Colaborador"] = relationship(  # noqa: F821
        back_populates="mediciones"
    )
    indicador: Mapped["Indicador"] = relationship(back_populates="mediciones", lazy="selectin")
