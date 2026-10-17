# -*- coding: utf-8 -*-
"""Datos iniciales y de demostracion

Aquí se crean los permisos, los roles, el usuario admin, el catálogo de
indicadores y la versión 1 de los criterios
"""
import random
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    AccionPlan,
    Colaborador,
    ConfiguracionEvaluacion,
    Direccion,
    EstadoPlan,
    Indicador,
    MedicionIndicador,
    Permiso,
    PlanDesarrollo,
    Rol,
    TipoIndicador,
    Usuario,
    Validez,
)
from app.services.area_evaluacion_service import asegurar_areas

PERMISOS: dict[str, str] = {
    "usuarios.gestionar": "Gestionar usuarios, roles y permisos",
    "colaboradores.gestionar": "Crear, actualizar y desactivar colaboradores",
    "colaboradores.consultar": "Consultar colaboradores y perfiles",
    "indicadores.gestionar": "Administrar indicadores y mediciones",
    "evaluaciones.ejecutar": "Ejecutar el flujo de evaluación",
    "evaluaciones.revisar": "Revisar resultados y registrar observaciones",
    "configuracion.gestionar": "Configurar criterios, pesos y umbrales",
    "reportes.consultar": "Ver paneles y reportes",
    "reportes.exportar": "Exportar reportes",
    "auditoria.consultar": "Consultar el registro de auditoría",
    "ia.usar": "Usar consultas y explicaciones asistidas por IA",
    "planes.consultar": "Consultar planes de desarrollo y sucesión",
    "planes.gestionar": "Administrar planes de desarrollo y sucesión",
}

ROLES: dict[str, list[str]] = {
    "ADMINISTRADOR": list(PERMISOS.keys()),
    "GESTOR_TALENTO": [
        "colaboradores.gestionar", "colaboradores.consultar", "indicadores.gestionar",
        "evaluaciones.ejecutar", "evaluaciones.revisar", "configuracion.gestionar",
        "reportes.consultar", "reportes.exportar", "ia.usar",
        "planes.consultar", "planes.gestionar",
    ],
    "EVALUADOR": [
        "colaboradores.consultar", "evaluaciones.ejecutar", "evaluaciones.revisar",
        "reportes.consultar", "ia.usar", "planes.consultar",
    ],
    "CONSULTA": ["colaboradores.consultar", "reportes.consultar"],
}

INDICADORES_BASE: list[tuple[str, str, TipoIndicador, Direccion]] = [
    ("DESEMPENO_GLOBAL", "Desempeño global", TipoIndicador.DESEMPENO, Direccion.MAYOR_MEJOR),
    ("CRECIMIENTO_DESEMPENO", "Crecimiento de desempeño vs. periodo anterior", TipoIndicador.DESEMPENO, Direccion.MAYOR_MEJOR),
    ("LIDERAZGO", "Competencia de liderazgo", TipoIndicador.COMPETENCIA, Direccion.MAYOR_MEJOR),
    ("COMUNICACION", "Competencia de comunicación", TipoIndicador.COMPETENCIA, Direccion.MAYOR_MEJOR),
    ("COLABORACION", "Competencia de colaboración", TipoIndicador.COMPETENCIA, Direccion.MAYOR_MEJOR),
    ("PUNTAJE_CAPACITACION", "Puntaje promedio de capacitación", TipoIndicador.CAPACITACION, Direccion.MAYOR_MEJOR),
    ("CURSOS_APROBADOS", "Cursos aprobados (normalizado 0-100)", TipoIndicador.CAPACITACION, Direccion.MAYOR_MEJOR),
    ("ANIOS_EXPERIENCIA", "Años de experiencia (normalizado)", TipoIndicador.EXPERIENCIA, Direccion.MAYOR_MEJOR),
    ("CUMPLIMIENTO_OBJETIVOS", "Cumplimiento de objetivos", TipoIndicador.OBJETIVO, Direccion.MAYOR_MEJOR),
    ("IMPACTO_PROYECTOS", "Impacto en proyectos organizacionales", TipoIndicador.ORGANIZACIONAL, Direccion.MAYOR_MEJOR),
    ("ROTACION_EQUIPO", "Rotación del equipo a cargo", TipoIndicador.ORGANIZACIONAL, Direccion.MENOR_MEJOR),
]

PESOS_V1: dict[str, float] = {
    "DESEMPENO_GLOBAL": 0.20, "CRECIMIENTO_DESEMPENO": 0.10, "LIDERAZGO": 0.12,
    "COMUNICACION": 0.08, "COLABORACION": 0.06, "PUNTAJE_CAPACITACION": 0.10,
    "CURSOS_APROBADOS": 0.05, "ANIOS_EXPERIENCIA": 0.07, "CUMPLIMIENTO_OBJETIVOS": 0.12,
    "IMPACTO_PROYECTOS": 0.06, "ROTACION_EQUIPO": 0.04,
}

COLABORADORES_DEMO: list[tuple[str, str, str, str, date, float]] = [
    ("COL-001", "Ana Sofía Mendoza Reyes", "Tecnología", "Desarrolladora Senior", date(2019, 3, 11), 0.90),
    ("COL-002", "Carlos Emilio Ramírez Soto", "Tecnología", "Ingeniero de Datos", date(2021, 7, 5), 0.72),
    ("COL-003", "Lucía Fernanda Ortiz Cruz", "Tecnología", "Desarrolladora Frontend", date(2022, 1, 17), 0.55),
    ("COL-004", "Diego Alejandro Torres Lima", "Recursos Humanos", "Especialista de Talento", date(2020, 9, 21), 0.70),
    ("COL-005", "María José Vargas Nieto", "Recursos Humanos", "Socio de negocio", date(2018, 2, 12), 0.88),
    ("COL-006", "Jorge Luis Salgado Prieto", "Finanzas", "Analista Financiero", date(2023, 4, 3), 0.50),
    ("COL-007", "Valeria Campos Domínguez", "Finanzas", "Contralora", date(2017, 11, 27), 0.92),
    ("COL-008", "Rodrigo Esteban Navarro León", "Comercial", "Ejecutivo de Cuentas", date(2022, 8, 15), 0.60),
    ("COL-009", "Daniela Paola Ríos Castañeda", "Comercial", "Gerente Comercial", date(2019, 6, 10), 0.85),
    ("COL-010", "Fernando Miguel Ávila Santos", "Operaciones", "Coordinador de Operaciones", date(2021, 1, 25), 0.58),
    ("COL-011", "Regina Ocampo Ruiz", "Operaciones", "Analista de Procesos", date(2023, 10, 2), 0.68),
    ("COL-012", "Pablo Adrián Quiroz Mena", "Operaciones", "Técnico de Soporte", date(2024, 5, 20), 0.42),
]

USUARIOS_DEMO: list[tuple[str, str, str, str]] = [
    ("Gestora de Talento", "gestor@develop.com.mx", "Gestor123!", "GESTOR_TALENTO"),
    ("Evaluador Líder", "evaluador@develop.com.mx", "Evaluador123!", "EVALUADOR"),
    ("Usuario Consulta", "consulta@develop.com.mx", "Consulta123!", "CONSULTA"),
]

PERIODOS_DEMO = ["2025-S2", "2026-S1"]

# Rangos de escala por indicador (min, max)
ESCALAS: dict[str, tuple[float, float]] = {
    "ANIOS_EXPERIENCIA": (1.0, 25.0),
    "ROTACION_EQUIPO": (2.0, 30.0),
}


def _valor_demo(codigo: str, base: float, rng: random.Random) -> float:
    mn, mx = ESCALAS.get(codigo, (40.0, 100.0))
    valor = mn + base * (mx - mn) + rng.uniform(-6.0, 6.0)
    return round(min(max(valor, mn), mx), 2)


def _validez_demo(rng: random.Random) -> Validez:
    # Casi todas las mediciones quedan validas; algunas quedan pendientes o
    # invalidas para probar que el proceso las excluye.
    dado = rng.random()
    if dado < 0.92:
        return Validez.VALIDA
    if dado < 0.97:
        return Validez.PENDIENTE
    return Validez.INVALIDA


def _planes_demo(colabs: list[Colaborador], admin_id: int) -> list[PlanDesarrollo]:
    """Planes de desarrollo/sucesión de ejemplo (liderazgo y desarrollo)."""
    por_codigo = {c.codigo: c for c in colabs}
    plantillas: list[tuple[str, str, str, date, date, list[tuple[str, date | None, bool]]]] = [
        (
            "COL-001", "Ruta de sucesión a Tech Lead", "liderazgo",
            date(2026, 1, 15), date(2026, 12, 15),
            [
                ("Programa de liderazgo de equipos ágiles", date(2026, 6, 30), False),
                ("Mentoría a dos desarrolladoras junior", date(2026, 9, 30), True),
                ("Liderar la migración del pipeline de datos", date(2026, 10, 31), True),
            ],
        ),
        (
            "COL-005", "Preparación para Dirección de Personas", "liderazgo",
            date(2026, 3, 1), date(2026, 11, 30),
            [
                ("Certificación en People Analytics", date(2026, 8, 31), False),
                ("Rotación como socio de negocio senior", date(2026, 7, 15), True),
                ("Presentar propuesta de modelo de competencias", date(2026, 5, 31), True),
            ],
        ),
        (
            "COL-007", "Desarrollo como Contralora Corporativa", "especialista",
            date(2025, 10, 1), date(2026, 8, 31),
            [
                ("Diplomado en finanzas corporativas", date(2026, 4, 30), True),
                ("Automatizar el cierre contable mensual", date(2026, 2, 28), False),
            ],
        ),
        (
            "COL-009", "Plan de sucesión comercial", "liderazgo",
            date(2026, 5, 1), date(2026, 12, 31),
            [
                ("Certificación en gestión de cuentas clave", date(2026, 9, 30), False),
                ("Presentar plan anual de crecimiento a dirección", date(2026, 11, 15), False),
            ],
        ),
        (
            "COL-012", "Fortalecimiento de competencias base", "desarrollo",
            date(2026, 6, 1), date(2026, 10, 31),
            [
                ("Curso de comunicación efectiva", date(2026, 8, 15), False),
            ],
        ),
    ]
    planes = []
    for codigo, titulo, foco, inicio, fin, acciones in plantillas:
        plan = PlanDesarrollo(
            colaborador_id=por_codigo[codigo].id,
            titulo=titulo,
            objetivo=(
                f"Preparar a {por_codigo[codigo].nombre} para mayores responsabilidades "
                "mediante acciones de desarrollo trazables."
            ),
            foco=foco,
            fecha_inicio=inicio,
            fecha_fin=fin,
            creado_por_id=admin_id,
        )
        completadas = 0
        for descripcion, limite, completada in acciones:
            plan.acciones.append(
                AccionPlan(descripcion=descripcion, fecha_limite=limite, completada=completada)
            )
            completadas += 1 if completada else 0
        total = len(acciones)
        plan.progreso = round(completadas * 100.0 / total, 1)
        if 0 < plan.progreso < 100:
            plan.estado = EstadoPlan.EN_PROGRESO
        elif plan.progreso >= 100:
            plan.estado = EstadoPlan.COMPLETADO
        planes.append(plan)
    return planes


def _asegurar_permisos_nuevos(db: Session) -> None:
    """Agrega permisos nuevos a bases ya sembradas (migración ligera).

    Permite que instalaciones existentes (p. ej. talento.db local) reciban
    los permisos de planes sin resembrar todo.
    """
    existentes = {p.codigo: p for p in db.scalars(select(Permiso))}
    faltantes = [
        Permiso(codigo=codigo, descripcion=desc)
        for codigo, desc in PERMISOS.items()
        if codigo not in existentes
    ]
    if not faltantes:
        return
    db.add_all(faltantes)
    db.flush()
    mapa = {p.codigo: p for p in faltantes}
    entrega: dict[str, list[str]] = {
        "ADMINISTRADOR": list(mapa.keys()),
        "GESTOR_TALENTO": ["planes.consultar", "planes.gestionar"],
        "EVALUADOR": ["planes.consultar"],
    }
    for nombre_rol, codigos in entrega.items():
        rol = db.scalars(select(Rol).where(Rol.nombre == nombre_rol)).first()
        if rol is None:
            continue
        actuales = {p.codigo for p in rol.permisos}
        rol.permisos.extend(mapa[c] for c in codigos if c in mapa and c not in actuales)
    db.commit()


def _asegurar_planes_demo(db: Session) -> None:
    """Siembra planes de ejemplo en bases ya sembradas sin ninguno."""
    if not settings.seed_demo_data:
        return
    if db.scalars(select(PlanDesarrollo).limit(1)).first() is not None:
        return
    colabs = list(db.scalars(select(Colaborador).order_by(Colaborador.codigo)))
    if not colabs:
        return
    admin = db.scalars(
        select(Usuario).where(Usuario.correo == settings.admin_email)
    ).first()
    if admin is None:
        return
    db.add_all(_planes_demo(colabs, admin.id))
    db.commit()


def sembrar(db: Session) -> None:
    """Siembra solo si la base está vacía (se puede re-ejecutar sin miedo)."""
    if db.scalars(select(Rol).limit(1)).first() is not None:
        # Base ya sembrada: aplica migraciones ligeras (permisos y planes demo).
        _asegurar_permisos_nuevos(db)
        _asegurar_planes_demo(db)
        asegurar_areas(db)
        return

    # --- Permisos y roles ---
    permisos = {
        codigo: Permiso(codigo=codigo, descripcion=desc) for codigo, desc in PERMISOS.items()
    }
    db.add_all(permisos.values())
    roles: dict[str, Rol] = {}
    for nombre, codigos in ROLES.items():
        rol = Rol(nombre=nombre, descripcion=f"Rol {nombre.title()}")
        rol.permisos = [permisos[c] for c in codigos]
        roles[nombre] = rol
    db.add_all(roles.values())
    db.flush()

    # --- Usuario administrador (siempre) ---
    admin = Usuario(
        nombre="Administrador del Sistema",
        correo=settings.admin_email,
        password_hash=hash_password(settings.admin_password),
        rol_id=roles["ADMINISTRADOR"].id,
    )
    db.add(admin)
    db.flush()

    # --- Indicadores base ---
    indicadores = {
        codigo: Indicador(codigo=codigo, nombre=nombre, tipo=tipo, direccion=direccion)
        for codigo, nombre, tipo, direccion in INDICADORES_BASE
    }
    db.add_all(indicadores.values())

    # Configuracion v1 activa.
    cfg = ConfiguracionEvaluacion(
        version=1,
        nombre="Criterios HiPo v1 — cuadro de mando de talento",
        criterios={"pesos": PESOS_V1},
        reglas={"cobertura_minima": 0.8, "umbral_desarrollo_rel": 0.85},
        umbral_hipo=75.0,
        activa=True,
        creado_por_id=admin.id,
    )
    db.add(cfg)

    # Datos de demostracion, si estan habilitados.
    if settings.seed_demo_data:
        rng = random.Random(2026)
        for nombre, correo, password, rol in USUARIOS_DEMO:
            db.add(
                Usuario(
                    nombre=nombre,
                    correo=correo,
                    password_hash=hash_password(password),
                    rol_id=roles[rol].id,
                )
            )
        colabs = [
            Colaborador(
                codigo=codigo, nombre=nombre, area=area, puesto=puesto,
                fecha_ingreso=ingreso,
            )
            for codigo, nombre, area, puesto, ingreso, _ in COLABORADORES_DEMO
        ]
        db.add_all(colabs)
        db.flush()

        for (codigo, _, _, _, _, base), colab in zip(COLABORADORES_DEMO, colabs, strict=True):
            for periodo in PERIODOS_DEMO:
                # COL-012 en 2026-S1 tiene datos insuficientes (RN-02)
                limitar = codigo == "COL-012" and periodo == "2026-S1"
                codigos_periodo = list(PESOS_V1.keys())[:4] if limitar else list(PESOS_V1.keys())
                for cod in codigos_periodo:
                    validez = _validez_demo(rng)
                    if limitar and cod in ("DESEMPENO_GLOBAL", "CUMPLIMIENTO_OBJETIVOS"):
                        validez = Validez.VALIDA
                    db.add(
                        MedicionIndicador(
                            colaborador_id=colab.id,
                            indicador_id=indicadores[cod].id,
                            periodo=periodo,
                            valor=_valor_demo(cod, base, rng),
                            validez=validez,
                        )
                    )

        # Planes de desarrollo/sucesion de demostracio
        db.add_all(_planes_demo(colabs, admin.id))
    db.commit()
    asegurar_areas(db)
