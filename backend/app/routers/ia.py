# -*- coding: utf-8 -*-
"""Consultas asistidas por IA (RF-08). Solo contexto autorizado."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import UserContext, require_permission
from app.db.base import get_db
from app.models import Colaborador, Evaluacion
from app.schemas import ConsultaAsistidaRequest, ConsultaAsistidaResponse
from app.services import ia_service

router = APIRouter(prefix="/ia", tags=["IA asistida"])


def _contexto_autorizado(db: Session, colaborador_id: int | None, periodo: str | None) -> str:
    """Construye el contexto mínimo y autorizado para la IA (RNF-03)."""
    partes: list[str] = []
    if colaborador_id:
        colab = db.get(Colaborador, colaborador_id)
        if colab:
            partes.append(
                f"Colaborador: {colab.nombre} ({colab.area}, {colab.puesto})."
            )
            evaluaciones = db.scalars(
                select(Evaluacion)
                .where(Evaluacion.colaborador_id == colaborador_id)
                .order_by(Evaluacion.fecha.desc())
                .limit(5)
            ).all()
            for ev in evaluaciones:
                if periodo and ev.periodo != periodo:
                    continue
                res = ev.resultado
                if res:
                    partes.append(
                        f"- Periodo {ev.periodo}: puntuación {res.puntuacion}, "
                        f"clasificación {res.clasificacion.value if res.clasificacion else 'n/d'}, "
                        f"cobertura {res.cobertura:.0%}."
                    )
    elif periodo:
        filas = db.execute(
            select(Evaluacion).where(Evaluacion.periodo == periodo)
        ).scalars().all()
        total = len(filas)
        hipo = sum(
            1 for ev in filas if ev.resultado and ev.resultado.clasificacion is not None
            and ev.resultado.clasificacion.value == "alto_potencial"
        )
        partes.append(f"Periodo {periodo}: {total} evaluaciones, {hipo} de alto potencial.")
    return "\n".join(partes) or "Sin datos autorizados disponibles para esta consulta."


@router.post("/consulta", response_model=ConsultaAsistidaResponse, summary="Consulta asistida")
def consulta_asistida(
    peticion: ConsultaAsistidaRequest,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_permission("ia.usar")),
):
    contexto = _contexto_autorizado(db, peticion.colaborador_id, peticion.periodo)
    respuesta, origen, advertencia = ia_service.consulta_asistida(
        peticion.pregunta, contexto
    )
    return ConsultaAsistidaResponse(respuesta=respuesta, origen=origen, advertencia=advertencia)
