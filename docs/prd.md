# Producto Requirements Document (PRD) — Sistema de Identificación de Talento de Alto Potencial

PRD — Product Requirements Document

Sistema de Identificación de Talento de Alto Potencial

PluriOne S.A. de C.V. — Develop Talent & Technology

### 0. Control del documento

| Campo | Valor |
|---|---|
| Producto | Sistema de Identificación de Talento de Alto Potencial (HiPo) |
| Versión del documento | 1.0 (aprobada) |
| Fecha | 10/11/2026 |
| Autor | Carlos Antonio Chapulín Segundo |
| Organización | PluriOne S.A. de C.V. · Develop Talent & Technology |
| Asesor empresarial | Juan Méndez Herrera |
| Líder de proyecto / evaluaciones | Edgar Loheffelmman |
| Estado | Aprobado — baseline del producto implementado (v1.1) |
| Documentos relacionados | Requerimientos · Propuesta técnica · Arquitectura · Desarrollo · Cómo funciona el proyecto |

Historial de versiones:

| Versión | Fecha | Autor | Descripción del cambio |
|---|---|---|---|
| 0.1 | 22/09/2026 | C. Chapulín | Borrador inicial a partir del documento de requerimientos y la propuesta técnica. |
| 1.0 | 10/11/2026 | C. Chapulín | Versión aprobada: incorpora historias de usuario, criterios de aceptación, métricas, riesgos, roadmap y trazabilidad RF → implementación. |

### 1. Resumen ejecutivo y visión del producto

### 1.1 Problema

Los procesos de sucesión, liderazgo y desarrollo del talento se apoyan en criterios dispersos y poco trazables: la información de desempeño, competencias, capacitación, experiencia, objetivos y métricas organizacionales vive en fuentes heterogéneas, sin validación común ni histórico comparable. Como consecuencia, identificar talento de alto potencial es lento, poco reproducible y difícil de justificar ante los interesados.

### 1.2 Solución propuesta

Un sistema web que centraliza la información de los colaboradores, valida su calidad, aplica un pipeline analítico configurable (normalización, puntuación ponderada y clasificación por umbrales), explica cada resultado con sus factores principales e integra IA asistida (Azure OpenAI) — siempre con revisión humana obligatoria y auditoría completa. El resultado es información estructurada y trazable que fortalece las soluciones de People Analytics de la organización.

### 1.3 Propuesta de valor

Trazabilidad total: cada resultado conserva factores, pesos, versión del modelo, criterios, fecha y revisiones humanas.

Reproducibilidad: criterios versionados; el histórico nunca se sobrescribe.

Calidad de datos por diseño: solo mediciones validadas participan; la carga masiva CSV valida fila por fila antes de registrar.

IA responsable: explicaciones y consultas asistidas con contexto mínimo autorizado, degradación elegante sin credenciales y decisión final humana.

Acción directa sobre el negocio: matriz 9-box, comparador de talento y planes de desarrollo con avance automático y alertas de riesgo.

### 2. Objetivos del producto y métricas de éxito

### 2.1 Objetivo general

Desarrollar un sistema inteligente que identifique colaboradores con alto potencial a partir del análisis de desempeño, competencias, capacitación, experiencia, objetivos y métricas organizacionales, con resultados trazables y revisión humana obligatoria.

### 2.2 Objetivos específicos y métricas

| Objetivo | Métrica de éxito (KPI) | Meta |
|---|---|---|
| Centralizar y validar los datos de talento | % de mediciones válidas al ejecutar una evaluación | ≥ 90 % |
| Reducir el tiempo de identificación de talento | Tiempo desde carga de datos hasta clasificación revisada | ≤ 1 día hábil por periodo |
| Garantizar trazabilidad de cada resultado | % de resultados con factores, versión del modelo y explicación | 100 % |
| Asegurar decisiones con revisión humana | % de resultados confirmados o marcados pendientes por un revisor | 100 % en 5 días hábiles |
| Apoyar la sucesión y el desarrollo | % de colaboradores HiPo con plan de desarrollo activo | ≥ 80 % |
| Adopción del sistema | Usuarios activos mensuales por rol autorizado | ≥ 70 % de usuarios autorizados |

### 2.3 No objetivos (fuera de esta versión)

Sustituir el juicio humano: el sistema aporta insumos; la decisión es de las personas.

Gestión de nómina, reclutamiento o evaluación 360° como módulos del producto.

Modelo predictivo entrenado a medida (se entrega puntuación por reglas versionada y el aislamiento necesario para conectar Azure ML en el futuro).

Integración automática con sistemas de RRHH externos (importación manual CSV).

### 3. Usuarios, roles y permisos (RBAC)

El acceso se controla mediante roles con permisos granulares; el backend valida cada llamada y el frontend oculta lo no autorizado (RNF-02).

| Rol | Quién es | Puede | No puede |
|---|---|---|---|
| ADMINISTRADOR | TI / responsable del sistema | Todo: usuarios, roles, configuración, auditoría, evaluaciones, reportes, IA y planes | — |
| GESTOR_TALENTO | Responsable de talento / HRBP | Colaboradores, indicadores y carga de datos, ejecutar evaluaciones, revisar, configurar criterios, reportes y exportar, IA, planes | Gestionar usuarios ni ver auditoría completa |
| EVALUADOR | Líderes que evalúan | Consultar colaboradores, ejecutar evaluaciones, revisar y observar, reportes, IA, consultar planes | Cargar datos, configurar criterios, exportar, gestionar usuarios |
| CONSULTA | Dirección / interesados | Consultar colaboradores, paneles y reportes | Cualquier operación de escritura, exportar ni usar IA |

Permisos atómicos del sistema (13): usuarios.gestionar · colaboradores.gestionar · colaboradores.consultar · indicadores.gestionar · evaluaciones.ejecutar · evaluaciones.revisar · configuracion.gestionar · reportes.consultar · reportes.exportar · auditoria.consultar · ia.usar · planes.consultar · planes.gestionar.

### 4. Alcance del producto

### 4.1 Dentro del alcance (v1.0)

Autenticación con JWT y control de acceso RBAC con 4 roles.

Gestión de colaboradores (CRUD con baja lógica) y perfil consolidado.

Catálogo de indicadores de 6 tipos y mediciones por periodo con estados de validez.

Carga de mediciones individual/bulk y carga masiva CSV con validación fila por fila.

Pipeline de evaluación HiPo: normalización min-max, puntuación ponderada y clasificación configurable con cobertura mínima.

Explicaciones y consultas asistidas por IA (Azure OpenAI) con modo local determinista.

Revisión humana de resultados y observaciones.

Reportes: dashboard, exportación CSV, matriz 9-box, comparador y centro de alertas.

Planes de desarrollo y sucesión con acciones, avance automático y riesgo.

Configuración versionada de criterios, pesos y umbrales.

Auditoría persistente de operaciones críticas.

Despliegue con Docker Compose y CI con GitHub Actions.

### 4.2 Fuera del alcance (v1.0)

Power BI embebido (las visualizaciones se entregan con componentes web propios).

Puntuación mediante Azure Machine Learning (la arquitectura lo deja preparado).

SSO / directorio corporativo, notificaciones por correo, aplicación móvil.

Migración automática desde sistemas de RRHH heredados.

### 5. Requisitos funcionales (RF)

Prioridad MoSCoW: M = Must (imprescindible) · S = Should (importante) · C = Could (deseable). Todos los requisitos M y S están implementados en la versión 1.0 del producto.

| ID | Requerimiento | Descripción | Prio. |
|---|---|---|---|
| RF-01 | Autenticación de usuarios | Inicio de sesión con credenciales validadas contra registros autorizados antes de acceder a los módulos. | M |
| RF-02 | Gestión de roles y permisos | Control de acceso basado en roles (RBAC) asociando permisos a administración, consulta, evaluación y reportes. | M |
| RF-03 | Gestión de colaboradores | Crear, consultar, actualizar y desactivar colaboradores (CRUD) sobre PostgreSQL con baja lógica que conserva histórico. | M |
| RF-04 | Gestión de indicadores | Administrar indicadores de desempeño, competencias, capacitación, experiencia, objetivos y métricas organizacionales. | M |
| RF-05 | Cálculo de indicadores | Procesar los datos disponibles y calcular variables derivadas (normalización min-max por población del periodo). | M |
| RF-06 | Identificación de alto potencial | Aplicar reglas/criterios definidos para clasificar a los colaboradores (alto potencial, en desarrollo, estándar, no evaluable). | M |
| RF-07 | Modelos analíticos y predictivos | Integrar modelos de Azure ML; en v1.0 la puntuación es determinista por reglas versionadas (reglas-v1) aislada para su sustitución. | S |
| RF-08 | Asistencia mediante IA | Integrar Azure OpenAI para explicaciones y consultas asistidas con contexto autorizado y degradación elegante a modo local. | S |
| RF-09 | Trazabilidad del resultado | Mostrar factores principales, fecha de evaluación y versión del modelo de cada resultado. | M |
| RF-10 | Consulta de perfil del colaborador | Vista consolidada con datos, mediciones, evaluaciones, resultados e historial según permisos. | M |

| ID | Requerimiento | Descripción | Prio. |
|---|---|---|---|
| RF-11 | Búsqueda y filtrado | Búsquedas y filtros por área, puesto, clasificación, periodo y otros atributos, con paginación. | M |
| RF-12 | Generación de reportes | Reportes de resultados e indicadores de talento con opciones de consulta, comparación (2-6 colaboradores) y matriz de sucesión 9-box. | M |
| RF-13 | Visualización de indicadores | Dashboards y visualizaciones de tendencias, distribuciones y métricas mediante componentes web (SVG). | M |
| RF-14 | Exportación de resultados | Exportar reportes a CSV respetando los permisos del usuario que realiza la operación. | M |
| RF-15 | Registro de auditoría | Registrar eventos relevantes (login, altas, cambios, exportaciones, configuración) con usuario y fecha/hora. | M |
| RF-16 | Configuración de criterios | Permitir a usuarios autorizados configurar criterios, ponderaciones y umbrales con versionado y una sola versión activa. | M |
| RF-17 | Histórico de evaluaciones | Conservar los resultados por periodo sin sobrescribir registros anteriores, con consulta y comparación histórica. | M |
| RF-18 | Revisión humana de resultados | Permitir a un usuario autorizado confirmar o marcar como pendiente un resultado generado por reglas, modelos o IA. | M |
| RF-19 | Registro de observaciones | Agregar comentarios asociados a una evaluación o colaborador, con autor, fecha y relación al registro. | S |

### 6. Requisitos no funcionales (RNF)

| ID | Requisito | Criterio verificable | Estado |
|---|---|---|---|
| RNF-01 | Seguridad de autenticación | Contraseñas con PBKDF2-SHA256 + sal; JWT con expiración (8 h). | Cumplido |
| RNF-02 | Control de acceso | RBAC validado en cada endpoint del backend y menú/rutas filtradas en el frontend; 401/403 según rol. | Cumplido |
| RNF-03 | Protección de datos | La IA solo recibe contexto mínimo autorizado; campos visibles según rol. | Cumplido |
| RNF-04 | Auditoría y trazabilidad | Toda operación crítica persiste quién, cuándo y sobre qué recurso. | Cumplido |
| RNF-05 | Confidencialidad de información | Secretos por variables de entorno; sin credenciales en el código. | Cumplido |
| RNF-06 | Rendimiento de consultas | Índices en columnas de filtro, paginación y lazy loading selectin. | Cumplido |
| RNF-07 | Concurrencia | Sesiones por petición con SQLAlchemy; despliegue escalable en contenedores. | Cumplido |
| RNF-08 | Usabilidad | Navegación consistente, mensajes de error comprensibles y formularios validados en React. | Cumplido |
| RNF-09 | Mantenibilidad | Capas separadas (core/db/models/schemas/services/routers) y frontend modular. | Cumplido |
| RNF-10 | Integración y despliegue continuo | GitHub Actions: pruebas pytest del servidor + build de la interfaz. | Cumplido |
| RNF-11 | Escalabilidad | Docker Compose permite replicar servicios; lógica lista para separar la analítica. | Cumplido |
| RNF-12 | Respaldo y recuperación | Volumen persistente de PostgreSQL; procedimientos documentados en la guía de desarrollo. | Cumplido |
| RNF-13 | Disponibilidad y estabilidad | Healthcheck de la base y endpoint /api/health; manejo de errores y degradación de IA. | Cumplido |
| RNF-14 | Mantenimiento y soporte | Guía de desarrollo, documentación de operación y plan de soporte multinivel de la propuesta. | Cumplido |

### 7. Reglas de negocio (RN)

| ID | Regla | Comportamiento esperado en el producto |
|---|---|---|
| RN-01 | Validación de datos | Solo mediciones VALIDA participan en evaluaciones; recargar un valor lo regresa a PENDIENTE para revalidación. |
| RN-02 | Información insuficiente | Registros con cobertura menor a la mínima se marcan INCOMPLETOS y no se presentan como evaluaciones completas (NO_EVALUABLE sin datos válidos). |
| RN-03 | Criterios configurables | Umbral y criterios de clasificación configurables por usuarios autorizados, versionados y con una sola versión activa. |
| RN-04 | Trazabilidad de la evaluación | Cada evaluación conserva fecha, criterios, factores principales y versión del modelo. |
| RN-05 | Histórico inmutable | Las evaluaciones anteriores no se sobrescriben: se conservan por periodo y admiten comparación histórica. |
| RN-06 | Revisión humana | Los resultados pueden revisarse, confirmarse o marcarse pendientes por un usuario autorizado. |
| RN-07 | Permisos en toda operación | Consultas, modificaciones y exportaciones respetan los permisos del usuario. |
| RN-08 | Auditoría de cambios | Los cambios relevantes de configuración y operación quedan registrados en auditoría. |

### 8. Historias de usuario y criterios de aceptación

Épicas principales del backlog del producto. Cada historia sigue el formato «Como ⟨rol⟩ quiero ⟨objetivo⟩ para ⟨beneficio⟩».

### US-01 · Carga masiva de mediciones

Como GESTOR_TALENTO quiero cargar mediciones de un periodo mediante CSV para alimentar la evaluación sin capturas manuales.

Descargar una plantilla CSV con datos reales del sistema.

Validar el archivo antes de registrar (modo «solo validar») sin escribir datos.

El reporte indica líneas aceptadas/rechazadas con motivo y número de línea.

Solo se aceptan colaboradores activos, indicadores existentes y valores numéricos.

Recargar una combinación colaborador+indicador+periodo hace upsert y regresa la medición a PENDIENTE (RN-01).

La operación y sus totales quedan en auditoría (RN-08).

### US-02 · Ejecución de la evaluación HiPo

Como GESTOR_TALENTO quiero ejecutar la evaluación de un periodo para obtener la clasificación de talento de la población.

Se evalúa a todos los colaboradores activos (o solo uno, si se indica).

Solo participan mediciones VALIDA del periodo (RN-01).

La puntuación pondera los indicadores normalizados min-max 0-100.

La clasificación respeta el umbral y reglas de la versión activa (RN-03).

Cada resultado muestra factores, cobertura, fecha y versión del modelo (RN-04).

Reejecutar no sobrescribe el histórico (RN-05) y la ejecución queda auditada.

### US-03 · Revisión humana de resultados

Como EVALUADOR quiero confirmar o marcar pendiente un resultado con comentario para validar la clasificación antes de usarla.

Solo usuarios con permiso evaluaciones.revisar pueden revisar.

Se registra estado (confirmado/pendiente), comentario, autor y fecha.

El estado de revisión es visible en listados, detalle y dashboard.

Los resultados sin revisar alimentan el centro de alertas (RN-06).

### US-04 · Configuración de criterios versionada

Como GESTOR_TALENTO quiero crear y activar versiones de criterios para ajustar el modelo sin perder la trazabilidad.

Se definen pesos por indicador, umbral HiPo, cobertura mínima y umbral relativo.

El sistema valida indicadores existentes y suma de pesos positiva.

Solo una versión puede estar activa; activar otra desactiva la anterior (RN-03).

Las evaluaciones registran la versión usada (RN-04) y todo queda auditado.

### US-05 · Panel y matriz de sucesión

Como CONSULTA quiero consultar el panel y la matriz 9-box para conocer la distribución del talento por periodo.

KPIs: activos, evaluaciones del periodo, HiPo y revisiones pendientes.

Distribución por clasificación, promedios por área y evolución por periodos.

La matriz clasifica desempeño × potencial con terciles de la población.

Solo visible con permiso reportes.consultar.

### US-06 · Comparación de colaboradores

Como GESTOR_TALENTO quiero comparar de 2 a 6 colaboradores con sus indicadores normalizados para apoyar decisiones de sucesión.

Selección de 2 a 6 colaboradores y filtro por periodo.

Solo mediciones válidas; normalización min-max 0-100 entre comparados.

Vista de radar y tabla por indicador con valores crudos.

Se exige mínimo 2 colaboradores (error 422 en caso contrario).

### US-07 · Planes de desarrollo

Como GESTOR_TALENTO quiero gestionar planes y acciones de desarrollo para preparar sucesores con seguimiento automático.

Plan con colaborador, foco (liderazgo/especialista/desarrollo), fechas y responsable.

Acciones con fecha límite; marcar completadas recalcula el avance.

Al 100 % el plan se cierra como completado; desmarcar lo reabre.

Planes abiertos con acciones vencidas se marcan en riesgo y generan alertas.

### US-08 · Gestión de usuarios y auditoría

Como ADMINISTRADOR quiero gestionar usuarios y roles y consultar la auditoría para mantener el control del sistema.

Crear/actualizar usuarios con rol y estado; contraseñas nunca en claro.

Consultar roles con sus permisos.

Auditoría filtrable por acción o texto y paginada.

Cambios de rol aplican de inmediato (permisos se recargan por petición).

### US-09 · Consultas asistidas por IA

Como usuario con permiso ia.usar quiero hacer preguntas sobre el talento para obtener respuestas rápidas con contexto autorizado.

La IA recibe únicamente el contexto mínimo autorizado (RNF-03).

Respuesta con origen (azure_openai / local_determinista).

Sin credenciales o ante fallo, responde en modo local con advertencia clara.

Los prompts restringen inventar datos; la decisión final es humana.

### 9. Flujos de uso principales

### 9.1 Ciclo operativo por periodo

1) Preparación: el GESTOR_TALENTO carga mediciones (individual, bulk o CSV con validación) y valida la calidad (validez de cada medición).

2) Configuración: ajusta (si aplica) la versión de criterios, pesos y umbral.

3) Evaluación: ejecuta el pipeline HiPo del periodo.

4) Revisión: los EVALUADORES confirman o marcan pendiente cada resultado (apoyados en factores y explicación IA).

5) Acción: se generan planes de desarrollo para los HiPo y se sigue el avance; la matriz 9-box y el comparador apoyan la sucesión.

6) Seguimiento: dashboard, exportaciones y centro de alertas cierran el ciclo.

### 9.2 Flujo de la evaluación (interna)

mediciones válidas del periodo   → normalización min-max por indicador (menor_mejor invertido)   → puntuación ponderada 0-100 (solo pesos con dato)   → cobertura y clasificación (umbral/umbrales de la versión activa)   → factores principales + explicación (IA o modo local)   → persistencia por periodo (sin sobrescribir) + auditoría

### 9.3 Flujo de carga CSV

Descargar plantilla → llenar → «solo validar» → corregir rechazos → «validar y registrar» → confirmar reporte de carga (upsert RN-01).

### 10. Dependencias, supuestos y restricciones

### 10.1 Dependencias

Azure OpenAI Service (opcional): explicaciones y consultas asistidas; sin credenciales el producto funciona en modo local determinista.

PostgreSQL 16 en la implementación (SQLite en desarrollo local).

Node.js 20 y Python 3.12 para construir; Docker para operar.

Azure Machine Learning (futuro): sustituir/complementar la puntuación por reglas; la arquitectura ya la contempla (modelo versionado y aislado).

### 10.2 Supuestos

La organización aporta las mediciones por periodo (carga CSV o manual).

Los criterios iniciales (pesos v1 y umbral 75) los define Talento.

Los periodos siguen una nomenclatura tipo 2026-S1 / 2026-S2.

### 10.3 Restricciones

La clasificación final siempre requiere revisión humana (política del negocio).

El histórico de evaluaciones es inmutable (RN-05).

Secretos únicamente por variables de entorno (RNF-05).

Los cambios fuera del alcance inicial deben analizarse y aprobarse antes de incorporarse.

### 11. Criterios de aceptación y de lanzamiento

### 11.1 Criterios de aceptación funcionales

Los 19 requisitos funcionales (RF-01..RF-19) implementados y demostrables en la interfaz web y la API.

Las 8 reglas de negocio (RN-01..RN-08) verificables en el producto.

Los criterios de aceptación de las historias US-01..US-09 cumplidos.

### 11.2 Criterios de calidad para liberar (release)

| Criterio | Verificación | Estado |
|---|---|---|
| Suite automatizada en verde | 34 pruebas pytest (auth/RBAC, CRUD, evaluaciones, planes, reportes) | Cumplido |
| Verificación end-to-end de módulos | verificar_modulos_e2e.py: 11/11 módulos contra servidor real | Cumplido |
| Compilación de la interfaz | npm run build sin errores (Vite) | Cumplido |
| Despliegue contenerizado | docker compose config/build correcto (db+backend+frontend) | Cumplido |
| CI en verde | GitHub Actions: pruebas backend + build frontend | Cumplido |
| Documentación completa | Requerimientos, propuesta, arquitectura, desarrollo, guía de funcionamiento y este PRD | Cumplido |

### 12. Riesgos y mitigaciones

| Riesgo | Impacto | Prob. | Mitigación |
|---|---|---|---|
| Calidad deficiente de los datos cargados | Alto | Media | Validación fila por fila, estados de validez y centro de alertas. |
| Sesgo en la clasificación automática | Alto | Media | Revisión humana obligatoria, factores visibles y criterios configurables. |
| Dependencia del servicio de IA | Medio | Media | Degradación elegante a modo local determinista con origen marcado. |
| Baja adopción de los usuarios | Alto | Baja | Capacitación en la entrega, interfaz guiada y roles bien acotados. |
| Privacidad de datos de personas | Alto | Baja | RBAC granular, contexto mínimo a la IA y auditoría completa. |
| Cambios de alcance tardíos | Medio | Media | Baseline aprobada; cambios fuera de alcance se analizan y aprueban. |

### 13. Roadmap y liberaciones

| Versión | Alcance | Estado |
|---|---|---|
| v1.0 | Núcleo: autenticación/RBAC, colaboradores, indicadores, pipeline HiPo, revisión humana, reportes base, configuración y auditoría. | Liberada |
| v1.1 | Carga masiva CSV con reporte de validación, matriz 9-box, comparador con radar, planes de desarrollo y centro de alertas. | Liberada |
| v1.2 | Exportaciones adicionales (PDF/XLSX), notificaciones por correo de pendientes y mejoras de visualización. | Planificada |
| v2.0 | Puntuación con Azure Machine Learning, Power BI embebido, SSO y multi-idioma. | Visión futura |

### 14. Trazabilidad RF → implementación

Estado de cada requerimiento funcional en el producto liberado (v1.1):

| RF | Módulo / endpoint principal | Estado |
|---|---|---|
| RF-01 | auth: POST /api/auth/login, GET /api/auth/me | Implementado |
| RF-02 | usuarios + RBAC: roles, permisos y 403 por permiso | Implementado |
| RF-03 | colaboradores: CRUD con baja lógica | Implementado |
| RF-04 | indicadores: catálogo y mediciones | Implementado |
| RF-05 | evaluaciones: normalización min-max (evaluacion_service) | Implementado |
| RF-06 | evaluaciones: clasificación por umbrales | Implementado |
| RF-07 | puntuación versionada (reglas-v1) aislada para Azure ML | Parcial (diseño listo) |
| RF-08 | ia: consulta asistida + explicaciones con fallback local | Implementado |
| RF-09 | resultado con factores, fecha y versión del modelo | Implementado |
| RF-10 | colaboradores/{id}/perfil (consolidado) | Implementado |
| RF-11 | filtros y paginación en colaboradores/evaluaciones/planes | Implementado |
| RF-12 | reportes: dashboard, 9-box, comparador | Implementado |
| RF-13 | dashboard con gráficas SVG (tendencias y distribuciones) | Implementado |
| RF-14 | reportes/export/evaluaciones.csv con permiso de exportar | Implementado |
| RF-15 | auditoría: registro y consulta filtrable | Implementado |
| RF-16 | configuración: versiones, activación y reglas | Implementado |
| RF-17 | histórico por periodo sin sobrescribir | Implementado |
| RF-18 | revisiones: confirmar/marcar pendiente | Implementado |
| RF-19 | observaciones en evaluación y colaborador | Implementado |
