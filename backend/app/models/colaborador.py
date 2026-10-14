# -*- coding: utf-8 -*-
"""Maestro de personas: colaboradores evaluables (RF-03)."""
from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Colaborador(Base):
    __tablename__ = "colaborador"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(160), index=True)
    area: Mapped[str] = mapped_column(String(120), index=True)
    puesto: Mapped[str] = mapped_column(String(120), default="")
    fecha_ingreso: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    mediciones: Mapped[list["MedicionIndicador"]] = relationship(  # noqa: F821
        back_populates="colaborador", cascade="all, delete-orphan"
    )
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(  # noqa: F821
        back_populates="colaborador", cascade="all, delete-orphan"
    )
    observaciones: Mapped[list["Observacion"]] = relationship(  # noqa: F821
        back_populates="colaborador"
    )
