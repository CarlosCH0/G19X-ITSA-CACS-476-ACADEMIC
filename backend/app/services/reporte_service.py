# -*- coding: utf-8 -*-
"""Paneles, reportes y exportaciones (RF-12, RF-13, RF-14, RN-07). — MVP"""
import csv
import io
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Clasificacion,
    Colaborador,
    Evaluacion,
    ResultadoEvaluacion,
)


def _periodo_mas_reciente(db: Session) -> str | None:
    return db.scalar(select(func.max(Evaluacion.periodo)))


def dashboard(db: Session, periodo: str | None = None) -> dict:
    """Agregaciones para el panel de control (RF-13)."""
    periodo = periodo or _periodo_mas_reciente(db)

    total_activos = db.scalar(
        select(func.count()).select_from(Colaborador).where(Colaborador.estado.is_(True))
    ) or 0

    base = (
        select(Evaluacion, ResultadoEvaluacion, Colaborador)
        .join(ResultadoEvaluacion, ResultadoEvaluacion.evaluacion_id == Evaluacion.id)
        .join(Colaborador, Colaborador.id == Evaluacion.colaborador_id)
    )
    filas = db.execute(base).all()

    if periodo:
        filas = [f for f in filas if f[0].periodo == periodo]

    distribucion: dict[str, int] = {}
    por_area: dict[str, list[float]] = {}
    revision_estado: dict[str, int] = {"sin_revision": 0}
    for ev, res, colab in filas:
        clave = res.clasificacion.value if res.clasificacion else "sin_clasificacion"
        distribucion[clave] = distribucion.get(clave, 0) + 1
        por_area.setdefault(colab.area, [])
        if res.puntuacion is not None:
            por_area[colab.area].append(res.puntuacion)
        if res.revisiones:
            ultima = max(res.revisiones, key=lambda r: r.fecha)
            revision_estado[ultima.estado.value] = revision_estado.get(ultima.estado.value, 0) + 1
        else:
            revision_estado["sin_revision"] += 1

    promedios_area = [
        {
            "area": area,
            # Sin puntuaciones válidas en el área el promedio es nulo (no divide entre cero).
            "promedio": round(sum(v) / len(v), 2) if v else None,
            "evaluados": len(v),
        }
        for area, v in sorted(por_area.items())
    ]

    hipo = [f for f in filas if f[1].clasificacion == Clasificacion.ALTO_POTENCIAL]
    top = sorted(hipo, key=lambda f: (f[1].puntuacion or 0), reverse=True)[:10]
    top_hipo = [
        {
            "evaluacion_id": ev.id,
            "colaborador_id": colab.id,
            "codigo": colab.codigo,
            "nombre": colab.nombre,
            "area": colab.area,
            "puntuacion": res.puntuacion,
            "periodo": ev.periodo,
            "estado_revision": (
                max(res.revisiones, key=lambda r: r.fecha).estado.value
                if res.revisiones
                else "sin_revision"
            ),
        }
        for ev, res, colab in top
    ]

    por_periodo: dict[str, list[float]] = {}
    for ev, res, _ in db.execute(base).all():
        if res.puntuacion is not None:
            por_periodo.setdefault(ev.periodo, []).append(res.puntuacion)
    evolucion = [
        {"periodo": p, "promedio": round(sum(v) / len(v), 2), "evaluados": len(v)}
        for p, v in sorted(por_periodo.items())
    ]

    return {
        "periodo": periodo,
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "kpis": {
            "colaboradores_activos": total_activos,
            "evaluaciones_periodo": len(filas),
            "alto_potencial": distribucion.get(Clasificacion.ALTO_POTENCIAL.value, 0),
            "revisiones_pendientes": revision_estado.get("sin_revision", 0),
        },
        "distribucion_clasificacion": distribucion,
        "promedios_por_area": promedios_area,
        "revisiones": revision_estado,
        "top_alto_potencial": top_hipo,
        "evolucion_periodos": evolucion,
    }


def exportar_evaluaciones_csv(db: Session, periodo: str | None = None) -> str:
    """Exportación CSV de resultados (RF-14). Respeta permisos en el router."""
    consulta = (
        select(Evaluacion, ResultadoEvaluacion, Colaborador)
        .join(ResultadoEvaluacion, ResultadoEvaluacion.evaluacion_id == Evaluacion.id)
        .join(Colaborador, Colaborador.id == Evaluacion.colaborador_id)
        .order_by(Evaluacion.periodo, Colaborador.codigo)
    )
    filas = db.execute(consulta).all()
    if periodo:
        filas = [f for f in filas if f[0].periodo == periodo]

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(
        [
            "evaluacion_id", "colaborador_codigo", "colaborador_nombre", "area", "puesto",
            "periodo", "fecha_evaluacion", "version_modelo", "configuracion_version",
            "estado_evaluacion", "puntuacion", "clasificacion", "cobertura",
            "factores_principales", "estado_revision",
        ]
    )
    for ev, res, colab in filas:
        top = ", ".join(
            f"{f['nombre']}={f['contribucion']:.2f}" for f in (res.factores or [])[:3]
        )
        estado_rev = (
            max(res.revisiones, key=lambda r: r.fecha).estado.value if res.revisiones else ""
        )
        writer.writerow(
            [
                ev.id, colab.codigo, colab.nombre, colab.area, colab.puesto,
                ev.periodo, ev.fecha.isoformat() if ev.fecha else "", ev.version_modelo,
                ev.configuracion.version if ev.configuracion else "",
                ev.estado.value, res.puntuacion if res.puntuacion is not None else "",
                res.clasificacion.value if res.clasificacion else "",
                f"{res.cobertura * 100:.0f}%", top, estado_rev,
            ]
        )
    return buffer.getvalue()
