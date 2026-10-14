# -*- coding: utf-8 -*-
"""Capa de persistencia: motor, sesión y base declarativa (SQLAlchemy 2.x)."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos del sistema."""


_conectar_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_conectar_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: sesión por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
