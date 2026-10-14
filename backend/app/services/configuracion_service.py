# -*- coding: utf-8 -*-
"""Configuración de criterios de evaluación versionada (RF-16, RN-03, RN-08)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import UserContext
from app.models import ConfiguracionEvaluacion, Indicador
from app.schemas import ConfiguracionCreate
from app.services import auditoria_service


def listar(db: Session) -> list[ConfiguracionEvaluacion]:
    return list(
        db.scalars(select(ConfiguracionEvaluacion).order_by(ConfiguracionEvaluacion.version.desc()))
    )


def obtener_activa(db: Session) -> ConfiguracionEvaluacion | None:
    return db.scalars(
        select(ConfiguracionEvaluacion).where(ConfiguracionEvaluacion.activa.is_(True))
    ).first()


def crear_version(
    db: Session, usuario: UserContext, datos: ConfiguracionCreate
) -> ConfiguracionEvaluacion:
    """Crea una nueva versión; opcionalmente la activa (solo una activa)."""
    codigos = list(datos.pesos.keys())
    existentes = {
        i.codigo for i in db.scalars(select(Indicador).where(Indicador.codigo.in_(codigos)))
    }
    faltantes = [c for c in codigos if c not in existentes]
    if faltantes:
        raise ValueError(f"Indicadores inexistentes en los pesos: {', '.join(faltantes)}")
    total = sum(datos.pesos.values())
    if total <= 0:
        raise ValueError("La suma de pesos debe ser mayor que cero")

    if datos.activar:
        for otra in db.scalars(
            select(ConfiguracionEvaluacion).where(ConfiguracionEvaluacion.activa.is_(True))
        ):
            otra.activa = False

    ultima = db.scalar(
        select(ConfiguracionEvaluacion.version).order_by(ConfiguracionEvaluacion.version.desc())
    )
    cfg = ConfiguracionEvaluacion(
        version=(ultima or 0) + 1,
        nombre=datos.nombre,
        criterios={"pesos": datos.pesos},
        reglas={
            "cobertura_minima": datos.cobertura_minima,
            "umbral_desarrollo_rel": datos.umbral_desarrollo_rel,
        },
        umbral_hipo=datos.umbral_hipo,
        activa=datos.activar,
        creado_por_id=usuario.id,
    )
    db.add(cfg)
    db.flush()
    auditoria_service.registrar(
        db, accion="configuracion.crear", recurso=f"configuracion:v{cfg.version}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={
            "version": cfg.version, "activa": datos.activar,
            "umbral_hipo": cfg.umbral_hipo, "pesos": datos.pesos,
        },
    )
    db.commit()
    db.refresh(cfg)
    return cfg


def activar(db: Session, usuario: UserContext, configuracion_id: int) -> ConfiguracionEvaluacion | None:
    cfg = db.get(ConfiguracionEvaluacion, configuracion_id)
    if cfg is None:
        return None
    for otra in db.scalars(
        select(ConfiguracionEvaluacion).where(
            ConfiguracionEvaluacion.activa.is_(True),
            ConfiguracionEvaluacion.id != cfg.id,
        )
    ):
        otra.activa = False
    cfg.activa = True
    auditoria_service.registrar(
        db, accion="configuracion.activar", recurso=f"configuracion:v{cfg.version}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
    )
    db.commit()
    db.refresh(cfg)
    return cfg
