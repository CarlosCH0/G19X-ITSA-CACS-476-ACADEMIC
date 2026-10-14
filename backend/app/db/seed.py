# -*- coding: utf-8 -*-
"""Datos iniciales y de demostración (solo primer arranque).

Crea: permisos, roles RBAC, usuario administrador, catálogo de indicadores y
la versión 1 de la configuración de criterios. Si SEED_DEMO_DATA=true agrega
usuarios de prueba, colaboradores y mediciones de dos periodos.
"""
import random
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    Colaborador,
    ConfiguracionEvaluacion,
    Direccion,
    Indicador,
    MedicionIndicador,
    Permiso,
    Rol,
    TipoIndicador,
    Usuario,
    Validez,
)

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
}

ROLES: dict[str, list[str]] = {
    "ADMINISTRADOR": list(PERMISOS.keys()),
    "GESTOR_TALENTO": [
        "colaboradores.gestionar", "colaboradores.consultar", "indicadores.gestionar",
        "evaluaciones.ejecutar", "evaluaciones.revisar", "configuracion.gestionar",
        "reportes.consultar", "reportes.exportar",
    ],
    "EVALUADOR": [
        "colaboradores.consultar", "evaluaciones.ejecutar", "evaluaciones.revisar",
        "reportes.consultar",
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
    dado = rng.random()
    if dado < 0.92:
        return Validez.VALIDA
    if dado < 0.97:
        return Validez.PENDIENTE
    return Validez.INVALIDA


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
    }
    for nombre_rol, codigos in entrega.items():
        rol = db.scalars(select(Rol).where(Rol.nombre == nombre_rol)).first()
        if rol is None:
            continue
        actuales = {p.codigo for p in rol.permisos}
        rol.permisos.extend(mapa[c] for c in codigos if c in mapa and c not in actuales)
    db.commit()


def sembrar(db: Session) -> None:
    """Idempotente: solo crea datos si la base está vacía."""
    if db.scalars(select(Rol).limit(1)).first() is not None:
        # Base ya sembrada: aplica migraciones ligeras (permisos nuevos).
        _asegurar_permisos_nuevos(db)
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

    # --- Configuración v1 (activa) ---
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

    # --- Datos de demostración opcionales ---
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
    db.commit()
