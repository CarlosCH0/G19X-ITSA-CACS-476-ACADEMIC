# -*- coding: utf-8 -*-
"""Gestión de indicadores y mediciones (RF-04, RN-01, RN-02). — MVP"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import UserContext
from app.models import Colaborador, Indicador, MedicionIndicador, Validez
from app.schemas import IndicadorCreate, IndicadorUpdate, MedicionBulkRequest
from app.services import auditoria_service


def listar_indicadores(db: Session, solo_activos: bool = False) -> list[Indicador]:
    consulta = select(Indicador).order_by(Indicador.tipo, Indicador.codigo)
    if solo_activos:
        consulta = consulta.where(Indicador.activo.is_(True))
    return list(db.scalars(consulta))


def crear_indicador(db: Session, usuario: UserContext, datos: IndicadorCreate) -> Indicador:
    if db.scalars(select(Indicador).where(Indicador.codigo == datos.codigo)).first():
        raise ValueError(f"Ya existe el indicador {datos.codigo}")
    ind = Indicador(**datos.model_dump())
    db.add(ind)
    db.flush()
    auditoria_service.registrar(
        db, accion="indicador.crear", recurso=f"indicador:{ind.codigo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
    )
    db.commit()
    db.refresh(ind)
    return ind


def actualizar_indicador(
    db: Session, usuario: UserContext, indicador_id: int, datos: IndicadorUpdate
) -> Indicador | None:
    ind = db.get(Indicador, indicador_id)
    if ind is None:
        return None
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(ind, campo, valor)
    auditoria_service.registrar(
        db, accion="indicador.actualizar", recurso=f"indicador:{ind.codigo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
    )
    db.commit()
    db.refresh(ind)
    return ind


def registrar_mediciones(
    db: Session, usuario: UserContext, peticion: MedicionBulkRequest
) -> list[MedicionIndicador]:
    """Carga por colaborador/periodo; upsert sobre la combinación única.

    RN-01: recargar un valor regresa la medición a PENDIENTE para revalidación.
    """
    if db.get(Colaborador, peticion.colaborador_id) is None:
        raise ValueError("Colaborador inexistente")
    existentes = {
        m.indicador_id: m
        for m in db.scalars(
            select(MedicionIndicador).where(
                MedicionIndicador.colaborador_id == peticion.colaborador_id,
                MedicionIndicador.periodo == peticion.periodo,
            )
        )
    }
    resultado: list[MedicionIndicador] = []
    for entrada in peticion.mediciones:
        if db.get(Indicador, entrada.indicador_id) is None:
            raise ValueError(f"Indicador inexistente: {entrada.indicador_id}")
        m = existentes.get(entrada.indicador_id)
        if m:
            m.valor = entrada.valor
            m.validez = entrada.validez
            m.comentario = entrada.comentario
        else:
            m = MedicionIndicador(
                colaborador_id=peticion.colaborador_id,
                indicador_id=entrada.indicador_id,
                periodo=peticion.periodo,
                valor=entrada.valor,
                validez=entrada.validez,
                comentario=entrada.comentario,
            )
            db.add(m)
        resultado.append(m)
    auditoria_service.registrar(
        db, accion="medicion.cargar",
        recurso=f"colaborador:{peticion.colaborador_id}/{peticion.periodo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={"cantidad": len(peticion.mediciones)},
    )
    db.commit()
    return resultado


def cambiar_validez(
    db: Session,
    usuario: UserContext,
    medicion_id: int,
    validez: Validez,
    comentario: str = "",
) -> MedicionIndicador | None:
    m = db.get(MedicionIndicador, medicion_id)
    if m is None:
        return None
    m.validez = validez
    m.comentario = comentario or m.comentario
    auditoria_service.registrar(
        db, accion="medicion.validez", recurso=f"medicion:{medicion_id}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={"validez": validez.value},
    )
    db.commit()
    db.refresh(m)
    return m


def mediciones_de_colaborador(
    db: Session, colaborador_id: int, periodo: str | None = None
) -> list[MedicionIndicador]:
    consulta = select(MedicionIndicador).where(
        MedicionIndicador.colaborador_id == colaborador_id
    )
    if periodo:
        consulta = consulta.where(MedicionIndicador.periodo == periodo)
    return list(
        db.scalars(consulta.order_by(MedicionIndicador.periodo, MedicionIndicador.indicador_id))
    )


def periodos_disponibles(db: Session) -> list[str]:
    filas = db.execute(
        select(MedicionIndicador.periodo, func.count())
        .group_by(MedicionIndicador.periodo)
        .order_by(MedicionIndicador.periodo)
    ).all()
    return [f[0] for f in filas]
