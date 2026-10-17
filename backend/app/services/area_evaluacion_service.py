# -*- coding: utf-8 -*-
"""Asignación de indicadores de evaluación por área."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import UserContext
from app.models import AreaEvaluacion, Colaborador, ConfiguracionEvaluacion, Indicador
from app.schemas import AreaPruebasUpdate
from app.services import auditoria_service


def asegurar_areas(db: Session) -> list[AreaEvaluacion]:
    """Crea configuraciones iniciales con todos los indicadores activos."""
    areas_activas = set(
        db.scalars(
            select(Colaborador.area)
            .where(Colaborador.estado.is_(True))
            .distinct()
        )
    )
    if not areas_activas:
        return []

    configuraciones = {
        config.area: config
        for config in db.scalars(
            select(AreaEvaluacion).where(AreaEvaluacion.area.in_(areas_activas))
        )
    }
    nuevas_areas = areas_activas.difference(configuraciones)
    if nuevas_areas:
        indicadores = list(
            db.scalars(select(Indicador).where(Indicador.activo.is_(True)))
        )
        for area in sorted(nuevas_areas):
            configuracion = AreaEvaluacion(area=area, indicadores=indicadores.copy())
            db.add(configuracion)
            configuraciones[area] = configuracion
        db.commit()

    return [configuraciones[area] for area in sorted(areas_activas)]


def listar(db: Session) -> dict:
    areas = asegurar_areas(db)
    configuracion_activa = db.scalars(
        select(ConfiguracionEvaluacion).where(ConfiguracionEvaluacion.activa.is_(True))
    ).first()
    pesos = (configuracion_activa.criterios or {}).get("pesos", {}) if configuracion_activa else {}
    indicadores = list(
        db.scalars(select(Indicador).order_by(Indicador.nombre, Indicador.codigo))
    )
    return {
        "areas": [
            {
                "area": area.area,
                "indicador_ids": sorted(indicador.id for indicador in area.indicadores),
            }
            for area in areas
        ],
        "indicadores": [
            {
                "id": indicador.id,
                "codigo": indicador.codigo,
                "nombre": indicador.nombre,
                "tipo": indicador.tipo.value,
                "activo": indicador.activo,
                "en_criterios": indicador.codigo in pesos,
            }
            for indicador in indicadores
        ],
    }


def actualizar(
    db: Session, usuario: UserContext, datos: AreaPruebasUpdate
) -> dict:
    asegurar_areas(db)
    configuracion = db.scalars(
        select(AreaEvaluacion).where(AreaEvaluacion.area == datos.area)
    ).first()
    if configuracion is None:
        raise ValueError("El área no tiene colaboradores activos o no existe.")

    nuevos_ids = set(datos.indicador_ids)
    if len(nuevos_ids) != len(datos.indicador_ids):
        raise ValueError("No se puede asignar un mismo indicador más de una vez.")

    indicadores = {
        indicador.id: indicador
        for indicador in db.scalars(
            select(Indicador).where(Indicador.id.in_(nuevos_ids))
        )
    } if nuevos_ids else {}
    faltantes = nuevos_ids.difference(indicadores)
    if faltantes:
        raise ValueError("Uno o más indicadores no existen.")

    actuales_ids = {indicador.id for indicador in configuracion.indicadores}
    nuevas_asignaciones = nuevos_ids.difference(actuales_ids)
    cfg_activa = db.scalars(
        select(ConfiguracionEvaluacion).where(ConfiguracionEvaluacion.activa.is_(True))
    ).first()
    pesos = (cfg_activa.criterios or {}).get("pesos", {}) if cfg_activa else {}
    no_disponibles = [
        indicadores[indicador_id].codigo
        for indicador_id in nuevas_asignaciones
        if not indicadores[indicador_id].activo
        or indicadores[indicador_id].codigo not in pesos
    ]
    if no_disponibles:
        raise ValueError(
            "Solo puedes agregar indicadores activos que tengan peso en la configuración "
            f"vigente: {', '.join(no_disponibles)}."
        )

    configuracion.indicadores = [
        indicadores[indicador_id] for indicador_id in datos.indicador_ids
    ]
    auditoria_service.registrar(
        db,
        accion="configuracion.area_pruebas",
        recurso=f"area:{configuracion.area}",
        usuario_id=usuario.id,
        usuario_nombre=usuario.nombre,
        detalle={
            "area": configuracion.area,
            "indicadores_anteriores": sorted(actuales_ids),
            "indicadores_nuevos": datos.indicador_ids,
        },
    )
    db.commit()
    return listar(db)
