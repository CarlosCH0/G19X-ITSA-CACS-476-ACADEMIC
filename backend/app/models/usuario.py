# -*- coding: utf-8 -*-
"""Entidades de seguridad: permisos, roles (RBAC) y usuarios."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Asociación N:M ROL — PERMISO
rol_permiso = Table(
    "rol_permiso",
    Base.metadata,
    Column("rol_id", ForeignKey("rol.id"), primary_key=True),
    Column("permiso_id", ForeignKey("permiso.id"), primary_key=True),
)


class Permiso(Base):
    __tablename__ = "permiso"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    descripcion: Mapped[str] = mapped_column(String(255), default="")


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    descripcion: Mapped[str] = mapped_column(String(255), default="")

    permisos: Mapped[list["Permiso"]] = relationship(
        secondary=rol_permiso, lazy="selectin"
    )
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"), index=True)
    estado: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rol: Mapped["Rol"] = relationship(back_populates="usuarios", lazy="selectin")
