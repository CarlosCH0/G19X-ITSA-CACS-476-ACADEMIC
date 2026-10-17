# -*- coding: utf-8 -*-
"""El flujo que identifica talento de alto potencial (el corazón del sistema).

Siguiendo el diagrama D4 del documento de arquitectura, cada ejecución hace:

1. Junta los datos del periodo y deja solo las mediciones válidas (RN-01, RN-02)
2. Normaliza cada indicador min-max dentro del área (RF-05)
3. Calcula la puntuación ponderada con los pesos de la configuración (RF-06, RF-07)
4. Clasifica comparando contra el umbral (RN-03)
5. Guarda los factores principales y genera la explicación (RF-08, RF-09)
6. Persiste todo por periodo —sin sobrescribir históricos— y registra auditoría
   (RN-04, RN-05)
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import UserContext
from app.models import (
    Clasificacion,
    AreaEvaluacion,
    Colaborador,
    ConfiguracionEvaluacion,
    Direccion,
    EstadoEvaluacion,
    EstadoRevision,
    Evaluacion,
    Indicador,
    MedicionIndicador,
    ResultadoEvaluacion,
    RevisionHumana,
    Validez,
)
from app.schemas import ResumenEjecucion
from app.services import area_evaluacion_service, auditoria_service, ia_service


class ErrorEvaluacion(Exception):
    """Violación de reglas de negocio del flujo."""


# ------------------------------------------------------------------
# Configuracion de criterios.
# ------------------------------------------------------------------
def obtener_configuracion(
    db: Session, configuracion_id: int | None = None
) -> ConfiguracionEvaluacion:
    if configuracion_id:
        cfg = db.get(ConfiguracionEvaluacion, configuracion_id)
        if cfg is None:
            raise ErrorEvaluacion(f"No existe la configuración {configuracion_id}")
        return cfg
    cfg = db.scalars(
        select(ConfiguracionEvaluacion).where(ConfiguracionEvaluacion.activa.is_(True))
    ).first()
    if cfg is None:
        raise ErrorEvaluacion(
            "No existe una configuración activa de criterios (RF-16). "
            "Crea una versión antes de ejecutar evaluaciones."
        )
    return cfg


def _estado_revision_de(resultado: ResultadoEvaluacion | None) -> EstadoRevision | None:
    """Última revisión humana del resultado (RF-18)."""
    if not resultado or not resultado.revisiones:
        return None
    ultima = max(resultado.revisiones, key=lambda r: r.fecha)
    return ultima.estado


# ------------------------------------------------------------------
# Ejecucion del proceso.
# ------------------------------------------------------------------
def ejecutar_evaluacion(
    db: Session,
    usuario: UserContext,
    periodo: str,
    colaborador_id: int | None = None,
    configuracion_id: int | None = None,
    generar_ia: bool = True,
) -> ResumenEjecucion:
    cfg = obtener_configuracion(db, configuracion_id)
    pesos: dict[str, float] = dict((cfg.criterios or {}).get("pesos", {}))
    if not pesos:
        raise ErrorEvaluacion("La configuración no define ponderaciones (pesos).")

    reglas = dict(cfg.reglas or {})
    cobertura_min = float(reglas.get("cobertura_minima", 0.8))
    umbral_dev_rel = float(reglas.get("umbral_desarrollo_rel", 0.85))

    # 1) Se toma la poblacion activa del periodo. Solo cuentan mediciones validas
    # (RN-01); las pendientes o invalidas no entran en el calculo.
    consulta = select(Colaborador).where(Colaborador.estado.is_(True))
    if colaborador_id:
        consulta = consulta.where(Colaborador.id == colaborador_id)
    colaboradores = list(db.scalars(consulta))
    if not colaboradores:
        raise ErrorEvaluacion("No hay colaboradores activos para evaluar.")
    ids = [c.id for c in colaboradores]

    area_evaluacion_service.asegurar_areas(db)
    configuraciones_area = db.scalars(
        select(AreaEvaluacion).where(AreaEvaluacion.area.in_({c.area for c in colaboradores}))
    ).all()
    pesos_por_area = {
        configuracion.area: {
            indicador.codigo: pesos[indicador.codigo]
            for indicador in configuracion.indicadores
            if indicador.activo and indicador.codigo in pesos
        }
        for configuracion in configuraciones_area
    }
    areas_sin_pruebas = sorted(
        {colab.area for colab in colaboradores if not pesos_por_area.get(colab.area)}
    )
    if areas_sin_pruebas:
        raise ErrorEvaluacion(
            "No hay pruebas activas con ponderación vigente para estas áreas: "
            f"{', '.join(areas_sin_pruebas)}. Configura sus pruebas o ponderaciones antes de evaluar."
        )

    codigos_pesos = sorted(
        {codigo for pesos_area in pesos_por_area.values() for codigo in pesos_area}
    )
    indicadores = {
        i.codigo: i
        for i in db.scalars(
            select(Indicador).where(
                Indicador.activo.is_(True), Indicador.codigo.in_(codigos_pesos)
            )
        )
    }
    mediciones = db.scalars(
        select(MedicionIndicador)
        .join(Indicador, MedicionIndicador.indicador_id == Indicador.id)
        .where(
            MedicionIndicador.periodo == periodo,
            MedicionIndicador.colaborador_id.in_(ids),
            Indicador.activo.is_(True),
            Indicador.codigo.in_(codigos_pesos),
            MedicionIndicador.validez == Validez.VALIDA,
        )
    ).all()

    valores: dict[int, dict[str, float]] = {cid: {} for cid in ids}
    areas_por_id = {colab.id: colab.area for colab in colaboradores}
    for m in mediciones:
        codigo = m.indicador.codigo
        if codigo in pesos_por_area[areas_por_id[m.colaborador_id]]:
            valores[m.colaborador_id][codigo] = float(m.valor)

    # 2. Se normaliza cada indicador dentro de su area.
    minimos: dict[tuple[str, str], float] = {}
    maximos: dict[tuple[str, str], float] = {}
    for area, pesos_area in pesos_por_area.items():
        ids_area = [colab.id for colab in colaboradores if colab.area == area]
        for codigo in pesos_area:
            serie = [valores[cid][codigo] for cid in ids_area if codigo in valores[cid]]
            if serie:
                minimos[(area, codigo)] = min(serie)
                maximos[(area, codigo)] = max(serie)

    def normalizar(area: str, codigo: str, valor: float) -> float:
        mn, mx = minimos[(area, codigo)], maximos[(area, codigo)]
        if mx == mn:
            return 0.5  # Si todos tienen el mismo valor, su aporte es neutro.
        n = (valor - mn) / (mx - mn)
        if indicadores[codigo].direccion == Direccion.MENOR_MEJOR:
            n = 1.0 - n
        return n

    # 3-5. Se calculan el puntaje, la clasificacion, los factores y la explicacion.
    ahora = datetime.now(timezone.utc)
    por_clasificacion: dict[str, int] = {}
    completos = incompletos = 0
    evaluacion_ids: list[int] = []

    for colab in colaboradores:
        disponibles = valores[colab.id]
        pesos_area = pesos_por_area[colab.area]
        cobertura = len(disponibles) / len(pesos_area) if pesos_area else 0.0

        factores: list[dict] = []
        suma_ponderada = 0.0
        suma_pesos = 0.0
        for codigo, peso in pesos_area.items():
            if codigo not in disponibles:
                continue
            ind = indicadores[codigo]
            norm = normalizar(colab.area, codigo, disponibles[codigo])
            contribucion = peso * norm
            suma_ponderada += contribucion
            suma_pesos += peso
            factores.append(
                {
                    "codigo": codigo,
                    "nombre": ind.nombre,
                    "tipo": ind.tipo.value,
                    "peso": round(peso, 4),
                    "valor": round(disponibles[codigo], 4),
                    "normalizado": round(norm, 4),
                    "contribucion": round(contribucion, 4),
                }
            )
        factores.sort(key=lambda f: f["contribucion"], reverse=True)

        # RN-02: si faltan datos, el resultado no se marca como evaluacion completa.
        es_completa = cobertura >= cobertura_min and suma_pesos > 0
        puntuacion = round(100.0 * suma_ponderada / suma_pesos, 2) if suma_pesos else None

        if not es_completa:
            clasificacion = Clasificacion.NO_EVALUABLE
        elif puntuacion >= cfg.umbral_hipo:
            clasificacion = Clasificacion.ALTO_POTENCIAL
        elif puntuacion >= cfg.umbral_hipo * umbral_dev_rel:
            clasificacion = Clasificacion.EN_DESARROLLO
        else:
            clasificacion = Clasificacion.ESTANDAR

        evaluacion = Evaluacion(
            colaborador_id=colab.id,
            configuracion_id=cfg.id,
            periodo=periodo,
            version_modelo=settings.modelo_version,
            estado=EstadoEvaluacion.COMPLETA if es_completa else EstadoEvaluacion.INCOMPLETA,
            ejecutado_por_id=usuario.id,
        )
        db.add(evaluacion)
        db.flush()

        resultado = ResultadoEvaluacion(
            evaluacion_id=evaluacion.id,
            puntuacion=puntuacion,
            clasificacion=clasificacion,
            cobertura=round(cobertura, 4),
            factores=factores,
        )
        if generar_ia and clasificacion != Clasificacion.NO_EVALUABLE:
            contexto = {
                "nombre": colab.nombre,
                "area": colab.area,
                "puesto": colab.puesto,
                "periodo": periodo,
                "puntuacion": puntuacion or 0,
                "clasificacion": clasificacion.value,
                "umbral": cfg.umbral_hipo,
                "cobertura_pct": f"{cobertura * 100:.0f}%",
                "factores_top": factores[:5],
                "version_modelo": settings.modelo_version,
            }
            texto, origen = ia_service.explicar_evaluacion(contexto)
            resultado.explicacion = texto
            resultado.explicacion_origen = origen
            resultado.fecha_explicacion = ahora
        db.add(resultado)

        evaluacion_ids.append(evaluacion.id)
        if es_completa:
            completos += 1
        else:
            incompletos += 1
        clave = clasificacion.value
        por_clasificacion[clave] = por_clasificacion.get(clave, 0) + 1

    auditoria_service.registrar(
        db,
        accion="evaluacion.ejecutar",
        recurso=f"periodo:{periodo}/config:v{cfg.version}",
        usuario_id=usuario.id,
        usuario_nombre=usuario.nombre,
        detalle={
            "periodo": periodo,
            "configuracion_version": cfg.version,
            "total": len(evaluacion_ids),
            "completos": completos,
            "incompletos": incompletos,
            "version_modelo": settings.modelo_version,
        },
    )
    db.commit()

    return ResumenEjecucion(
        periodo=periodo,
        configuracion_version=cfg.version,
        version_modelo=settings.modelo_version,
        total_evaluados=len(evaluacion_ids),
        completos=completos,
        incompletos=incompletos,
        por_clasificacion=por_clasificacion,
        evaluacion_ids=evaluacion_ids,
    )


# ------------------------------------------------------------------
# Consultas
# ------------------------------------------------------------------
def listar_evaluaciones(
    db: Session,
    *,
    periodo: str | None = None,
    clasificacion: str | None = None,
    area: str | None = None,
    colaborador_id: int | None = None,
    pagina: int = 1,
    tamanio: int = 20,
) -> tuple[list[dict], int]:
    """Listado paginado con filtros (RF-11, RF-17)."""
    consulta = (
        select(Evaluacion, ResultadoEvaluacion)
        .join(ResultadoEvaluacion, ResultadoEvaluacion.evaluacion_id == Evaluacion.id)
        .join(Colaborador, Colaborador.id == Evaluacion.colaborador_id)
    )
    if periodo:
        consulta = consulta.where(Evaluacion.periodo == periodo)
    if colaborador_id:
        consulta = consulta.where(Evaluacion.colaborador_id == colaborador_id)
    if area:
        consulta = consulta.where(Colaborador.area.ilike(f"%{area}%"))
    if clasificacion:
        consulta = consulta.where(ResultadoEvaluacion.clasificacion == clasificacion)
    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.execute(
        consulta.order_by(Evaluacion.fecha.desc()).offset((pagina - 1) * tamanio).limit(tamanio)
    ).all()

    items = []
    for ev, res in filas:
        items.append(
            {
                "id": ev.id,
                "colaborador_id": ev.colaborador_id,
                "colaborador_codigo": ev.colaborador.codigo,
                "colaborador_nombre": ev.colaborador.nombre,
                "area": ev.colaborador.area,
                "periodo": ev.periodo,
                "fecha": ev.fecha,
                "version_modelo": ev.version_modelo,
                "estado": ev.estado,
                "configuracion_version": ev.configuracion.version if ev.configuracion else 0,
                "puntuacion": res.puntuacion,
                "clasificacion": res.clasificacion,
                "estado_revision": _estado_revision_de(res),
            }
        )
    return items, total


def obtener_detalle(db: Session, evaluacion_id: int) -> Evaluacion | None:
    return db.get(Evaluacion, evaluacion_id)


def generar_explicacion(
    db: Session, usuario: UserContext, evaluacion_id: int
) -> ResultadoEvaluacion | None:
    """(Re)genera la explicación IA de una evaluación existente (RF-08, RF-09)."""
    ev = db.get(Evaluacion, evaluacion_id)
    if ev is None or ev.resultado is None:
        return None
    res = ev.resultado
    top = (res.factores or [])[:5]
    contexto = {
        "nombre": ev.colaborador.nombre,
        "area": ev.colaborador.area,
        "puesto": ev.colaborador.puesto,
        "periodo": ev.periodo,
        "puntuacion": res.puntuacion or 0,
        "clasificacion": res.clasificacion.value if res.clasificacion else "n/d",
        "umbral": ev.configuracion.umbral_hipo if ev.configuracion else 0,
        "cobertura_pct": f"{(res.cobertura or 0) * 100:.0f}%",
        "factores_top": top,
        "version_modelo": ev.version_modelo,
    }
    texto, origen = ia_service.explicar_evaluacion(contexto)
    res.explicacion = texto
    res.explicacion_origen = origen
    res.fecha_explicacion = datetime.now(timezone.utc)
    auditoria_service.registrar(
        db,
        accion="evaluacion.explicacion",
        recurso=f"evaluacion:{evaluacion_id}",
        usuario_id=usuario.id,
        usuario_nombre=usuario.nombre,
        detalle={"origen": origen},
    )
    db.commit()
    db.refresh(res)
    return res


def historial_colaborador(db: Session, colaborador_id: int) -> list[dict]:
    """Histórico por periodo sin sobrescribir (RF-17, RN-05)."""
    evaluaciones = db.scalars(
        select(Evaluacion)
        .where(Evaluacion.colaborador_id == colaborador_id)
        .order_by(Evaluacion.fecha.asc())
    ).all()
    historial = []
    for ev in evaluaciones:
        res = ev.resultado
        historial.append(
            {
                "evaluacion_id": ev.id,
                "periodo": ev.periodo,
                "fecha": ev.fecha,
                "estado": ev.estado,
                "version_modelo": ev.version_modelo,
                "puntuacion": res.puntuacion if res else None,
                "clasificacion": res.clasificacion.value if res and res.clasificacion else None,
            }
        )
    return historial
