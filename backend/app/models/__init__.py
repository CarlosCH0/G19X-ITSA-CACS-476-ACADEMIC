# -*- coding: utf-8 -*-
"""Modelos ORM del sistema (modelo entidad-relación del documento de arquitectura)."""
from app.models.usuario import Permiso, Rol, Usuario, rol_permiso
from app.models.colaborador import Colaborador
from app.models.plan import AccionPlan, EstadoPlan, PlanDesarrollo
from app.models.indicador import (
    AreaEvaluacion,
    Direccion,
    Indicador,
    MedicionIndicador,
    TipoIndicador,
    Validez,
)
from app.models.evaluacion import (
    Clasificacion,
    ConfiguracionEvaluacion,
    EstadoEvaluacion,
    EstadoRevision,
    Evaluacion,
    Observacion,
    ResultadoEvaluacion,
    RevisionHumana,
)
from app.models.auditoria import Auditoria

__all__ = [
    "Permiso", "Rol", "Usuario", "rol_permiso",
    "Colaborador",
    "AccionPlan", "EstadoPlan", "PlanDesarrollo",
    "AreaEvaluacion", "Direccion", "Indicador", "MedicionIndicador", "TipoIndicador", "Validez",
    "Clasificacion", "ConfiguracionEvaluacion", "EstadoEvaluacion", "EstadoRevision",
    "Evaluacion", "Observacion", "ResultadoEvaluacion", "RevisionHumana",
    "Auditoria",
]
