# -*- coding: utf-8 -*-
"""Gestión de colaboradores: CRUD, búsqueda/filtros y perfil consolidado
(RF-03, RF-10, RF-11, RF-17)."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import UserContext
from app.models import Colaborador, MedicionIndicador
from app.schemas import ColaboradorCreate, ColaboradorUpdate
from app.services import auditoria_service, evaluacion_service


def listar(
    db: Session,
    *,
    q: str | None = None,
    area: str | None = None,
    puesto: str | None = None,
    solo_activos: bool = True,
    pagina: int = 1,
    tamanio: int = 20,
) -> tuple[list[dict], int]:
    consulta = select(Colaborador)
    if solo_activos:
        consulta = consulta.where(Colaborador.estado.is_(True))
    if q:
        like = f"%{q}%"
        consulta = consulta.where(
            or_(Colaborador.nombre.ilike(like), Colaborador.codigo.ilike(like))
        )
    if area:
        consulta = consulta.where(Colaborador.area.ilike(f"%{area}%"))
    if puesto:
        consulta = consulta.where(Colaborador.puesto.ilike(f"%{puesto}%"))
    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    colaboradores = db.scalars(
        consulta.order_by(Colaborador.nombre.asc())
        .offset((pagina - 1) * tamanio)
        .limit(tamanio)
    ).all()

    items = []
    for c in colaboradores:
        ultima = None
        if c.evaluaciones:
            mejor = max(c.evaluaciones, key=lambda e: e.fecha)
            if mejor.resultado:
                ultima = mejor.resultado
        items.append(
            {
                "id": c.id,
                "codigo": c.codigo,
                "nombre": c.nombre,
                "area": c.area,
                "puesto": c.puesto,
                "fecha_ingreso": c.fecha_ingreso,
                "estado": c.estado,
                "ultima_puntuacion": ultima.puntuacion if ultima else None,
                "ultima_clasificacion": (
                    ultima.clasificacion.value if ultima and ultima.clasificacion else None
                ),
                "ultimo_periodo": mejor.periodo if ultima else None,
            }
        )
    return items, total


def obtener(db: Session, colaborador_id: int) -> Colaborador | None:
    return db.get(Colaborador, colaborador_id)


def crear(db: Session, usuario: UserContext, datos: ColaboradorCreate) -> Colaborador:
    if db.scalars(select(Colaborador).where(Colaborador.codigo == datos.codigo)).first():
        raise ValueError(f"Ya existe un colaborador con el código {datos.codigo}")
    colab = Colaborador(**datos.model_dump())
    db.add(colab)
    db.flush()
    auditoria_service.registrar(
        db, accion="colaborador.crear", recurso=f"colaborador:{colab.codigo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={"codigo": colab.codigo, "nombre": colab.nombre},
    )
    db.commit()
    db.refresh(colab)
    return colab


def actualizar(
    db: Session, usuario: UserContext, colaborador_id: int, datos: ColaboradorUpdate
) -> Colaborador | None:
    colab = db.get(Colaborador, colaborador_id)
    if colab is None:
        return None
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(colab, campo, valor)
    auditoria_service.registrar(
        db, accion="colaborador.actualizar", recurso=f"colaborador:{colab.codigo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre, detalle=datos.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(colab)
    return colab


def desactivar(db: Session, usuario: UserContext, colaborador_id: int) -> Colaborador | None:
    """Desactivación lógica (RF-03): el histórico se conserva."""
    colab = db.get(Colaborador, colaborador_id)
    if colab is None:
        return None
    colab.estado = False
    auditoria_service.registrar(
        db, accion="colaborador.desactivar", recurso=f"colaborador:{colab.codigo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
    )
    db.commit()
    db.refresh(colab)
    return colab


def perfil_consolidado(db: Session, colaborador_id: int) -> dict | None:
    """Vista consolidada del colaborador (RF-10)."""
    colab = db.get(Colaborador, colaborador_id)
    if colab is None:
        return None
    mediciones = db.scalars(
        select(MedicionIndicador)
        .where(MedicionIndicador.colaborador_id == colaborador_id)
        .order_by(MedicionIndicador.periodo.desc())
    ).all()
    return {
        "colaborador": colab,
        "mediciones": mediciones,
        "historial": evaluacion_service.historial_colaborador(db, colaborador_id),
    }
