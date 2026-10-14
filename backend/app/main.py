# -*- coding: utf-8 -*-
"""Punto de entrada de la API — Sistema de Identificación de Talento HiPo.

Arranque en desarrollo:
    uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base, SessionLocal, engine
from app.db.seed import sembrar
from app.routers import (
    auditoria,
    auth,
    colaboradores,
    configuracion,
    evaluaciones,
    indicadores,
    reportes,
    revisiones,
    usuarios,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Crea el esquema y siembra datos iniciales (idempotente)."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        sembrar(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "API para la identificación de colaboradores con alto potencial mediante "
        "análisis de desempeño, competencias, capacitación, experiencia, objetivos "
        "y métricas organizacionales. Incluye RBAC, trazabilidad, revisión humana "
        "e integración opcional con Azure OpenAI."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    usuarios.router,
    colaboradores.router,
    indicadores.router,
    evaluaciones.router,
    revisiones.router,
    reportes.router,
    configuracion.router,
    auditoria.router,
):
    app.include_router(router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", tags=["Salud"], summary="Verificación de salud")
def salud():
    return {
        "estado": "ok",
        "aplicacion": settings.app_name,
        "entorno": settings.entorno,
        "version_modelo": settings.modelo_version,
    }
