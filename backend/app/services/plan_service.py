# -*- coding: utf-8 -*-
"""Servicio de planes de desarrollo y sucesión (liderazgo, desarrollo, sucesión).

Reglas:
- El avance (progreso) se recalcula a partir de las acciones completadas.
- Un plan con acciones vencidas incompletas se marca "en riesgo".
- Toda operación relevante se registra en auditoría (RN-08).
"""
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import UserContext
from app.models import (
    AccionPlan,
    Colaborador,
    EstadoPlan,
    PlanDesarrollo,
    Usuario,
)
from app.schemas import PlanCreate, PlanUpdate
from app.services import auditoria_service

ESTADOS_ABIERTOS = (EstadoPlan.PLANIFICADO, EstadoPlan.EN_PROGRESO)


def _en_riesgo(plan: PlanDesarrollo, hoy: date) -> bool:
    """Plan abierto con acciones vencidas pendientes o fin ya pasado."""
    if plan.estado not in ESTADOS_ABIERTOS:
        return False
    if plan.fecha_fin < hoy:
        return True
    return any(
        (a.fecha_limite is not None and a.fecha_limite < hoy and not a.completada)
        for a in plan.acciones
    )


def _recalcular_progreso(plan: PlanDesarrollo) -> float:
    total = len(plan.acciones)
    if not total:
        return 0.0 if plan.estado == EstadoPlan.PLANIFICADO else (
            100.0 if plan.estado == EstadoPlan.COMPLETADO else 0.0
        )
    completadas = sum(1 for a in plan.acciones if a.completada)
    progreso = round(completadas * 100.0 / total, 1)
    plan.progreso = progreso
    if progreso >= 100.0 and plan.estado in ESTADOS_ABIERTOS:
        plan.estado = EstadoPlan.COMPLETADO
    elif 0 < progreso < 100:
        # Se vuelve a abrir el plan si se desmarca una accion o pasa a progreso.
        if plan.estado in (EstadoPlan.PLANIFICADO, EstadoPlan.COMPLETADO):
            plan.estado = EstadoPlan.EN_PROGRESO
    elif progreso == 0.0 and plan.estado == EstadoPlan.COMPLETADO:
        plan.estado = EstadoPlan.PLANIFICADO
    return progreso


def _a_listado(plan: PlanDesarrollo) -> dict:
    hoy = date.today()
    return {
        "id": plan.id,
        "colaborador_id": plan.colaborador_id,
        "titulo": plan.titulo,
        "objetivo": plan.objetivo,
        "foco": plan.foco,
        "fecha_inicio": plan.fecha_inicio,
        "fecha_fin": plan.fecha_fin,
        "estado": plan.estado,
        "progreso": plan.progreso,
        "responsable_id": plan.responsable_id,
        "creado_por_id": plan.creado_por_id,
        "fecha_creacion": plan.fecha_creacion,
        "total_acciones": len(plan.acciones),
        "acciones_completadas": sum(1 for a in plan.acciones if a.completada),
        "colaborador_codigo": plan.colaborador.codigo if plan.colaborador else "",
        "colaborador_nombre": plan.colaborador.nombre if plan.colaborador else "",
        "area": plan.colaborador.area if plan.colaborador else "",
        "responsable_nombre": plan.responsable.nombre if plan.responsable else "",
        "en_riesgo": _en_riesgo(plan, hoy),
    }


def _a_detalle(plan: PlanDesarrollo) -> dict:
    base = _a_listado(plan)
    base.update(
        {
            "puesto": plan.colaborador.puesto if plan.colaborador else "",
            "creado_por_nombre": plan.creado_por.nombre if plan.creado_por else "",
            "acciones": [
                {
                    "id": a.id,
                    "plan_id": a.plan_id,
                    "descripcion": a.descripcion,
                    "completada": a.completada,
                    "fecha_limite": a.fecha_limite,
                    "fecha_creacion": a.fecha_creacion,
                }
                for a in plan.acciones
            ],
        }
    )
    return base


def listar(
    db: Session,
    *,
    q: str | None = None,
    estado: str | None = None,
    area: str | None = None,
    colaborador_id: int | None = None,
    solo_abiertos: bool = False,
    pagina: int = 1,
    tamanio: int = 20,
) -> tuple[list[dict], int]:
    consulta = select(PlanDesarrollo).join(Colaborador)
    if q:
        like = f"%{q}%"
        consulta = consulta.where(
            (PlanDesarrollo.titulo.ilike(like))
            | (PlanDesarrollo.objetivo.ilike(like))
            | (Colaborador.nombre.ilike(like))
            | (Colaborador.codigo.ilike(like))
        )
    if estado:
        consulta = consulta.where(PlanDesarrollo.estado == EstadoPlan(estado))
    if area:
        consulta = consulta.where(Colaborador.area.ilike(f"%{area}%"))
    if colaborador_id:
        consulta = consulta.where(PlanDesarrollo.colaborador_id == colaborador_id)
    if solo_abiertos:
        consulta = consulta.where(PlanDesarrollo.estado.in_(ESTADOS_ABIERTOS))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    planes = list(
        db.scalars(
            consulta.order_by(PlanDesarrollo.fecha_fin.asc())
            .offset((pagina - 1) * tamanio)
            .limit(tamanio)
        )
    )
    return [_a_listado(p) for p in planes], total


def obtener_detalle(db: Session, plan_id: int) -> dict | None:
    plan = db.get(PlanDesarrollo, plan_id)
    return _a_detalle(plan) if plan else None


def estadisticas(db: Session) -> dict:
    planes = list(db.scalars(select(PlanDesarrollo)))
    hoy = date.today()
    por_estado: dict[str, int] = {}
    for p in planes:
        clave = p.estado.value
        por_estado[clave] = por_estado.get(clave, 0) + 1
    abiertos = [p for p in planes if p.estado in ESTADOS_ABIERTOS]
    return {
        "total": len(planes),
        "por_estado": por_estado,
        "avance_promedio": (
            round(sum(p.progreso for p in planes) / len(planes), 1) if planes else 0.0
        ),
        "en_riesgo": sum(1 for p in abiertos if _en_riesgo(p, hoy)),
        "vencidos": sum(1 for p in abiertos if p.fecha_fin < hoy),
    }


def crear(db: Session, usuario: UserContext, datos: PlanCreate) -> PlanDesarrollo:
    if db.get(Colaborador, datos.colaborador_id) is None:
        raise ValueError("Colaborador inexistente")
    if datos.responsable_id and db.get(Usuario, datos.responsable_id) is None:
        raise ValueError("Responsable inexistente")

    plan = PlanDesarrollo(
        colaborador_id=datos.colaborador_id,
        titulo=datos.titulo,
        objetivo=datos.objetivo,
        foco=datos.foco,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
        responsable_id=datos.responsable_id,
        creado_por_id=usuario.id,
    )
    for acc in datos.acciones:
        plan.acciones.append(
            AccionPlan(
                descripcion=acc.descripcion,
                fecha_limite=acc.fecha_limite,
                completada=acc.completada,
            )
        )
    db.add(plan)
    db.flush()
    _recalcular_progreso(plan)
    auditoria_service.registrar(
        db, accion="plan.crear", recurso=f"plan:{plan.id}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={
            "colaborador_id": plan.colaborador_id,
            "titulo": plan.titulo,
            "acciones": len(plan.acciones),
        },
    )
    db.commit()
    db.refresh(plan)
    return plan


def actualizar(
    db: Session, usuario: UserContext, plan_id: int, datos: PlanUpdate
) -> PlanDesarrollo | None:
    plan = db.get(PlanDesarrollo, plan_id)
    if plan is None:
        return None
    campos = datos.model_dump(exclude_unset=True)
    if "responsable_id" in campos and campos["responsable_id"] is not None:
        if db.get(Usuario, campos["responsable_id"]) is None:
            raise ValueError("Responsable inexistente")
    if "fecha_inicio" in campos or "fecha_fin" in campos:
        inicio = campos.get("fecha_inicio", plan.fecha_inicio)
        fin = campos.get("fecha_fin", plan.fecha_fin)
        if fin < inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
    for campo, valor in campos.items():
        setattr(plan, campo, valor)
    plan.fecha_actualizacion = datetime.now(timezone.utc)
    if plan.estado == EstadoPlan.COMPLETADO:
        plan.progreso = 100.0
    _recalcular_progreso(plan)
    auditoria_service.registrar(
        db, accion="plan.actualizar", recurso=f"plan:{plan.id}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={"campos": list(campos.keys())},
    )
    db.commit()
    db.refresh(plan)
    return plan


def agregar_accion(
    db: Session, usuario: UserContext, plan_id: int, descripcion: str,
    fecha_limite: date | None,
) -> AccionPlan | None:
    plan = db.get(PlanDesarrollo, plan_id)
    if plan is None:
        return None
    if plan.estado in (EstadoPlan.COMPLETADO, EstadoPlan.CANCELADO):
        raise ValueError("No se pueden agregar acciones a un plan cerrado")
    accion = AccionPlan(plan_id=plan_id, descripcion=descripcion, fecha_limite=fecha_limite)
    db.add(accion)
    db.flush()
    _recalcular_progreso(plan)
    auditoria_service.registrar(
        db, accion="plan.accion_agregar", recurso=f"plan:{plan_id}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
    )
    db.commit()
    db.refresh(accion)
    return accion


def marcar_accion(
    db: Session, usuario: UserContext, accion_id: int, completada: bool
) -> tuple[AccionPlan | None, PlanDesarrollo | None]:
    accion = db.get(AccionPlan, accion_id)
    if accion is None:
        return None, None
    accion.completada = completada
    plan = db.get(PlanDesarrollo, accion.plan_id)
    if plan:
        _recalcular_progreso(plan)
        auditoria_service.registrar(
            db, accion="plan.accion_marcar", recurso=f"plan:{plan.id}",
            usuario_id=usuario.id, usuario_nombre=usuario.nombre,
            detalle={"accion_id": accion_id, "completada": completada},
        )
    db.commit()
    if plan:
        db.refresh(plan)
    db.refresh(accion)
    return accion, plan


def eliminar(db: Session, usuario: UserContext, plan_id: int) -> PlanDesarrollo | None:
    plan = db.get(PlanDesarrollo, plan_id)
    if plan is None:
        return None
    db.delete(plan)
    auditoria_service.registrar(
        db, accion="plan.eliminar", recurso=f"plan:{plan_id}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={"titulo": plan.titulo},
    )
    db.commit()
    return plan


def planes_de_colaborador(db: Session, colaborador_id: int) -> list[dict]:
    planes = list(
        db.scalars(
            select(PlanDesarrollo)
            .where(PlanDesarrollo.colaborador_id == colaborador_id)
            .order_by(PlanDesarrollo.fecha_fin.desc())
        )
    )
    return [_a_listado(p) for p in planes]


def contar_planes_activos(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(PlanDesarrollo)
            .where(PlanDesarrollo.estado.in_(ESTADOS_ABIERTOS))
        )
        or 0
    )
