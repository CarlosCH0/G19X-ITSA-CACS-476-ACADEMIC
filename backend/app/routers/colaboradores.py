# -*- coding: utf-8 -*-
"""Gestión de colaboradores y perfil consolidado (RF-03, RF-10, RF-11, RF-17)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.schemas import (
    ColaboradorCreate,
    ColaboradorOut,
    ColaboradorUpdate,
    ObservacionCreate,
    ObservacionOut,
    PaginaColaboradores,
)
from app.services import colaborador_service, revision_service

router = APIRouter(prefix="/colaboradores", tags=["Colaboradores"])


@router.get("", response_model=PaginaColaboradores, summary="Buscar y filtrar (RF-11)")
def listar(
    q: str | None = None,
    area: str | None = None,
    puesto: str | None = None,
    incluir_inactivos: bool = False,
    pagina: int = 1,
    tamanio: int = 20,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("colaboradores.consultar")),
):
    items, total = colaborador_service.listar(
        db, q=q, area=area, puesto=puesto,
        solo_activos=not incluir_inactivos, pagina=pagina, tamanio=tamanio,
    )
    return PaginaColaboradores(total=total, pagina=pagina, tamanio=tamanio, items=items)


@router.post("", response_model=ColaboradorOut, status_code=201, summary="Crear (RF-03)")
def crear(
    datos: ColaboradorCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("colaboradores.gestionar")),
):
    try:
        return colaborador_service.crear(db, user, datos)
    except ValueError as e:
        raise HTTPException(409, str(e)) from e


@router.get("/{colaborador_id}", response_model=ColaboradorOut, summary="Consultar")
def obtener(
    colaborador_id: int,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("colaboradores.consultar")),
):
    colab = colaborador_service.obtener(db, colaborador_id)
    if colab is None:
        raise HTTPException(404, "Colaborador no encontrado")
    return colab


@router.put("/{colaborador_id}", response_model=ColaboradorOut, summary="Actualizar")
def actualizar(
    colaborador_id: int,
    datos: ColaboradorUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("colaboradores.gestionar")),
):
    colab = colaborador_service.actualizar(db, user, colaborador_id, datos)
    if colab is None:
        raise HTTPException(404, "Colaborador no encontrado")
    return colab


@router.delete("/{colaborador_id}", response_model=ColaboradorOut, summary="Desactivar")
def desactivar(
    colaborador_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("colaboradores.gestionar")),
):
    colab = colaborador_service.desactivar(db, user, colaborador_id)
    if colab is None:
        raise HTTPException(404, "Colaborador no encontrado")
    return colab


@router.get("/{colaborador_id}/perfil", summary="Perfil consolidado (RF-10)")
def perfil(
    colaborador_id: int,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("colaboradores.consultar")),
):
    perfil = colaborador_service.perfil_consolidado(db, colaborador_id)
    if perfil is None:
        raise HTTPException(404, "Colaborador no encontrado")
    colab = perfil["colaborador"]
    mediciones = [
        {
            "id": m.id,
            "indicador_id": m.indicador_id,
            "indicador_codigo": m.indicador.codigo,
            "indicador_nombre": m.indicador.nombre,
            "tipo": m.indicador.tipo.value,
            "periodo": m.periodo,
            "valor": m.valor,
            "validez": m.validez.value,
            "comentario": m.comentario,
        }
        for m in perfil["mediciones"]
    ]
    observaciones = [
        ObservacionOut(
            id=o.id, evaluacion_id=o.evaluacion_id, colaborador_id=o.colaborador_id,
            autor_id=o.autor_id, autor_nombre=o.autor.nombre if o.autor else "",
            texto=o.texto, fecha=o.fecha,
        )
        for o in revision_service.observaciones_de_colaborador(db, colaborador_id)
    ]
    return {
        "colaborador": ColaboradorOut.model_validate(colab),
        "mediciones": mediciones,
        "historial": perfil["historial"],
        "observaciones": observaciones,
    }


@router.get("/{colaborador_id}/historial", summary="Histórico (RF-17, RN-05)")
def historial(
    colaborador_id: int,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("colaboradores.consultar")),
):
    if colaborador_service.obtener(db, colaborador_id) is None:
        raise HTTPException(404, "Colaborador no encontrado")
    return colaborador_service.perfil_consolidado(db, colaborador_id)["historial"]


@router.post(
    "/{colaborador_id}/observaciones",
    response_model=ObservacionOut,
    status_code=201,
    summary="Observaciones del colaborador (RF-19)",
)
def observar_colaborador(
    colaborador_id: int,
    datos: ObservacionCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission("evaluaciones.revisar")),
):
    from app.models import Observacion

    if colaborador_service.obtener(db, colaborador_id) is None:
        raise HTTPException(404, "Colaborador no encontrado")
    obs = Observacion(colaborador_id=colaborador_id, autor_id=user.id, texto=datos.texto)
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return ObservacionOut(
        id=obs.id, evaluacion_id=None, colaborador_id=colaborador_id,
        autor_id=user.id, autor_nombre=user.nombre, texto=obs.texto, fecha=obs.fecha,
    )
