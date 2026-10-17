# Cómo funciona el proyecto — Guía completa del código

> Sistema de Identificación de Talento de Alto Potencial (HiPo) · PluriOne S.A. de C.V.
> Este documento explica **qué hace y cómo funciona cada parte** del código: backend,
> frontend, base de datos, despliegue y verificación.

## 1. Visión general

El sistema identifica colaboradores con **alto potencial** analizando desempeño,
competencias, capacitación, experiencia, objetivos y métricas organizacionales.
El resultado pasa siempre por **revisión humana** antes de tomarse decisiones.

**Stack tecnológico:**

| Capa | Tecnología | Rol |
|---|---|---|
| API / servidor | Python 3.12 + FastAPI | Lógica de negocio, RBAC, pipeline analítico |
| ORM / BD | SQLAlchemy 2.x + PostgreSQL (SQLite en desarrollo) | Persistencia |
| Contratos API | Pydantic v2 | Validación de entrada/salida |
| Interfaz web | React 18 + Vite (SPA, HashRouter) | Consumo de la API |
| IA (opcional) | Azure OpenAI Service | Explicaciones y consultas asistidas |
| Despliegue | Docker Compose (db + backend + frontend/nginx) | Empaquetado |
| CI | GitHub Actions | Pruebas pytest + build Vite |

**Principio de arquitectura en capas (backend):**

```
petición HTTP
   │
   ▼
routers/    → validan entrada (schemas/), sesión y permisos (core/deps)
   │
   ▼
services/   → reglas de negocio, cálculos, auditoría
   │
   ▼
models/     → entidades SQLAlchemy (ORM)
   │
   ▼
db/base.py  → motor y sesión → PostgreSQL / SQLite
```

Regla de oro: **los routers no calculan, los servicios no hablan HTTP**. Cada
capa es reutilizable y probable de forma aislada.

## 2. Estructura de carpetas

```
proyecto/
├── docker-compose.yml          # Orquesta db + backend + frontend
├── .env.example                # Variables de entorno de ejemplo
├── README.md                   # Resumen funcional del sistema
├── docs/                       # Documentación (este archivo, arquitectura, guía)
├── .github/workflows/ci.yml    # Integración continua
├── backend/
│   ├── Dockerfile              # Imagen Python (uvicorn)
│   ├── requirements.txt        # Dependencias fijadas
│   ├── app/
│   │   ├── main.py             # App FastAPI + arranque (lifespan)
│   │   ├── core/               # config, security (JWT/PBKDF2), deps (RBAC)
│   │   ├── db/                 # base (engine/sesión) y seed (datos iniciales)
│   │   ├── models/             # 13 entidades ORM
│   │   ├── schemas/            # Contratos Pydantic (entrada/salida)
│   │   ├── services/           # 10 servicios de negocio
│   │   └── routers/            # 11 routers HTTP
│   ├── tests/                  # pruebas pytest (incluye seguridad de configuración)
│   ├── smoke_e2e.py            # Smoke test manual contra servidor vivo
│   ├── verificar_modulos_e2e.py# Verificación E2E exhaustiva de módulos
│   └── verificar_vivo.py       # Verificación del stack desplegado (8081)
└── frontend/
    ├── Dockerfile              # Build multi-stage: node → nginx
    ├── nginx.conf              # Sirve la SPA y hace proxy /api → backend
    ├── vite.config.js          # Dev server + proxy /api → :8000
    └── src/
        ├── main.jsx            # Punto de entrada (HashRouter + AuthProvider)
        ├── App.jsx             # Rutas protegidas por permiso
        ├── api/client.js       # fetch con JWT, manejo de errores y descargas
        ├── context/AuthContext.jsx # Sesión en React + localStorage
        ├── components/Layout.jsx   # Menú lateral, barra superior, campana de alertas
        └── pages/              # 14 páginas (una por módulo funcional)
```

## 3. Backend — punto de entrada (`app/main.py`)

```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.entorno.casefold() not in {"produccion", "production"}:
        Base.metadata.create_all(bind=engine)  # solo desarrollo
    with SessionLocal() as db:
        sembrar(db)
    yield
```

- **`lifespan`**: en desarrollo crea tablas faltantes; en Docker, Alembic aplica
  migraciones antes de iniciar el servidor. Luego siembra permisos, roles, admin,
  indicadores, la configuración v1 de criterios y (si `SEED_DEMO_DATA=true`)
  usuarios, 12 colaboradores y mediciones de dos periodos.
- **CORS**: permite los orígenes del dev server de Vite (`5173`).
- **Routers**: se registran los 11 routers bajo el prefijo `/api`.
- **`/api/health`**: verifica estado, entorno, versión del modelo y si la IA
  está configurada (usado por el smoke test y Docker).

Arranque en desarrollo: `uvicorn app.main:app --reload --port 8000`
Documentación automática: `http://localhost:8000/docs` (OpenAPI/Swagger).

## 4. Backend — `core/` (configuración, seguridad y RBAC)

### `core/config.py`
Clase `Settings` (pydantic-settings) que lee variables de entorno o `.env`:
`DATABASE_URL`, `SECRET_KEY`, duración del token, credenciales de Azure OpenAI
(opcionales), datos del admin inicial y `MODELO_VERSION`. Se cachea con
`@lru_cache` (un solo objeto `settings` en todo el proceso).

### `core/security.py`
- **Contraseñas**: `hash_password` genera PBKDF2-SHA256 con sal aleatoria
  (`pbkdf2_sha256$iteraciones$sal$hash`); `verify_password` compara con
  `hmac.compare_digest` (inmune a timing attacks).
- **Tokens**: `create_access_token` emite un JWT HS256 con `sub` (id usuario),
  `rol`, `permisos`, `iat`, `jti` y `exp` (8 h por defecto).

## 5. Backend — `db/seed.py` (datos iniciales e idempotentes)

`sembrar(db)` se ejecuta en cada arranque:

1. **Si la base ya existe** (hay roles): aplica ajustes idempotentes de datos:
   `_asegurar_permisos_nuevos` (agrega permisos nuevos como `planes.*` a los
   roles que corresponden) y `_asegurar_planes_demo` (siembra planes de ejemplo
   si no hay ninguno). Nunca duplica datos.
2. **Si es una base nueva**: crea
   - **13 permisos** (`usuarios.gestionar`, `colaboradores.*`,
     `indicadores.gestionar`, `evaluaciones.*`, `configuracion.gestionar`,
     `reportes.*`, `auditoria.consultar`, `ia.usar`, `planes.*`).
   - **4 roles**: `ADMINISTRADOR` (todos), `GESTOR_TALENTO` (gestión completa
     de talento), `EVALUADOR` (ejecuta y revisa), `CONSULTA` (solo lectura).
   - **Usuario admin** con `ADMIN_EMAIL`/`ADMIN_PASSWORD` del entorno.
   - **11 indicadores base** de 6 tipos (desempeño, competencia, capacitación,
     experiencia, objetivo, organizacional) con su dirección
     (`MAYOR_MEJOR` o `MENOR_MEJOR`, p. ej. rotación de equipo).
   - **Configuración v1** de criterios: pesos por indicador, umbral HiPo 75,
     cobertura mínima 0.8 — queda **activa**.
   - **Si `SEED_DEMO_DATA=true`**: 3 usuarios demo (gestor, evaluador,
     consulta), 12 colaboradores, mediciones de `2025-S2` y `2026-S1`
     (deterministas, semilla fija), con validez mixta (algunas PENDIENTE para
     demostrar la regla RN-01) y `COL-012` con datos insuficientes en
     `2026-S1` (demuestra RN-02), más planes de desarrollo de ejemplo.

## 6. Backend — `models/` (entidades ORM)

| Archivo | Entidades | Qué representan |
|---|---|---|
| `usuario.py` | `Permiso`, `Rol`, `Usuario`, `rol_permiso` | Seguridad RBAC. `rol_permiso` es la tabla N:M. `Usuario.rol` se carga con `lazy="selectin"`. |
| `colaborador.py` | `Colaborador` | Maestro de personas: código único, nombre, área, puesto, fecha ingreso, estado (baja lógica). |
| `indicador.py` | `Indicador`, `MedicionIndicador` + enums `TipoIndicador`, `Direccion`, `Validez` | Catálogo y mediciones por periodo. Restricción única `(colaborador, indicador, periodo)` que habilita el *upsert*. `validez` ∈ {valida, pendiente, invalida}. |
| `evaluacion.py` | `ConfiguracionEvaluacion`, `Evaluacion`, `ResultadoEvaluacion`, `RevisionHumana`, `Observacion` + enums `EstadoEvaluacion`, `Clasificacion`, `EstadoRevision` | El corazón analítico. `ConfiguracionEvaluacion` versiona pesos (`criterios` JSON), reglas (`reglas` JSON) y umbral. `ResultadoEvaluacion` guarda puntuación, clasificación, cobertura, `factores` (JSON con el desglose por indicador) y la explicación IA. `RevisionHumana` es el histórico de confirmaciones. |
| `plan.py` | `PlanDesarrollo`, `AccionPlan` + enum `EstadoPlan` | Planes de sucesión con acciones; `progreso` se recalcula al marcar acciones. |
| `auditoria.py` | `Auditoria` | Quén (`usuario_id`/`usuario_nombre`), cuándo (`fecha_hora`), qué (`accion`, `recurso`) y detalle JSON. |

**Relaciones principales:**

```
Rol 1—N Usuario          Colaborador 1—N MedicionIndicador N—1 Indicador
Colaborador 1—N Evaluacion N—1 ConfiguracionEvaluacion
Evaluacion 1—1 ResultadoEvaluacion 1—N RevisionHumana
Colaborador 1—N PlanDesarrollo 1—N AccionPlan
```

  `decode_token` valida firma y expiración.

### `core/deps.py`
- `get_current_user` (dependencia FastAPI): extrae el JWT del header
  `Authorization: Bearer`, lo decodifica, carga el usuario **desde la BD**
  (los permisos siempre están vigentes, no solo los del token) y construye un
  `UserContext(id, nombre, correo, rol, permisos)`. Sin token o token inválido
  → `401`.
- `require_permission("x")`: fábrica de dependencias; si el rol del usuario no
  incluye el permiso → `403`. Es el corazón del **RBAC**.

### `db/base.py`
`engine` (creado según `DATABASE_URL`, con `check_same_thread=False` solo para
SQLite), `SessionLocal` (fábrica de sesiones) y `get_db` (dependencia que abre
una sesión por petición y la cierra al final).

## 7. Backend — `services/` (lógica de negocio)

### `evaluacion_service.py` — el pipeline HiPo
`ejecutar_evaluacion(db, usuario, periodo, ...)` recorre las etapas del
diagrama D4 de la arquitectura:

1. **Configuración**: toma la versión activa (o la indicada) y sus pesos.
   Después limita los indicadores a los asignados al área de cada colaborador.
   Si un área no tiene pruebas ponderadas → error 422 (RF-16).
2. **Población y datos**: colaboradores activos y sus mediciones del periodo
   **solo con validez = VALIDA** (RN-01).
3. **Variables derivadas**: normalización **min-max por indicador dentro del
   área** usando mín/máx de su población en el periodo. Si todos tienen el
   mismo valor → 0.5 (contribución neutra). Si el indicador es `MENOR_MEJOR`
   se invierte.
4. **Puntuación**: `100 × Σ(peso × normalizado) / Σ(pesos con dato)`.
   Cada factor queda registrado con valor crudo, normalizado, peso y
   contribución (esto alimenta los "factores principales" de RF-09).
5. **Clasificación** (según reglas de la configuración):
   - cobertura < mínima o sin datos → `NO_EVALUABLE` / estado INCOMPLETA
     (RN-02: nunca se presenta como equivalente a una completa),
   - puntuación ≥ `umbral_hipo` → `ALTO_POTENCIAL`,
   - puntuación ≥ `umbral_desarrollo_rel × umbral` → `EN_DESARROLLO`,
   - resto → `ESTANDAR`.
6. **Explicación IA** (opcional): se genera para los evaluables (ver
   `ia_service`).
7. **Persistencia**: crea `Evaluacion` + `ResultadoEvaluacion` NUEVOS por
   ejecución (RN-04/RN-05: nunca se sobrescribe el histórico), registra
   auditoría y devuelve un `ResumenEjecucion` con totales por clasificación.

Otras funciones: `listar_evaluaciones` (filtros + paginación),
`obtener_detalle`, `generar_explicacion` (regenera la explicación IA de una
evaluación existente) e `historial_colaborador` (histórico por periodo).

### `indicador_service.py`
CRUD del catálogo; `registrar_mediciones` (bulk por colaborador/periodo con
*upsert*: recargar un valor lo regresa a PENDIENTE, RN-01);
`cambiar_validez` (validar/invalidar con comentario, auditado);
`plantilla_csv` (CSV de ejemplo con datos reales) y `cargar_mediciones_csv`:
parsea el CSV (separador `;`), valida **fila por fila** (colaborador activo,
indicador existente, valor numérico, validez válida, periodo no vacío) y
devuelve un reporte con aceptadas/rechazadas/motivos y línea. Con
`validar_solo=True` no registra nada. La carga real hace upsert y audita.

### `colaborador_service.py`
CRUD con baja **lógica** (conserva histórico), búsqueda/filtros paginados
(`q` sobre nombre/código, área, puesto) enriquecida con la última evaluación,
y `perfil_consolidado`: colaborador + mediciones + histórico de evaluaciones
(RF-10).

### `revision_service.py`
`registrar_revision`: agrega una `RevisionHumana` (CONFIRMADO/PENDIENTE con
comentario, RF-18/RN-06); `agregar_observacion` y consulta de observaciones.

### `configuracion_service.py`
Versionado de criterios: valida que los indicadores de los pesos existan y la
suma sea > 0; garantiza **una sola versión activa** (desactiva las demás);
toda operación auditada (RN-03/RN-08).

### `area_evaluacion_service.py`
Mantiene el conjunto de indicadores que se evalúan para cada área. Al aparecer
un área nueva, se inicializa con todos los indicadores activos; después el
administrador o gestor puede personalizar su selección desde Configuración.
Solo se pueden agregar indicadores activos con peso en la versión vigente.
Cambiar una selección afecta ejecuciones futuras, no resultados históricos.

### `plan_service.py`
Planes y acciones. `_recalcular_progreso`: avance = acciones completadas /
total; al llegar a 100 % el plan se cierra como COMPLETADO; si se desmarca una
acción, el plan se reabre (EN_PROGRESO). `_en_riesgo`: plan abierto con
acciones vencidas pendientes o fecha fin superada. Validaciones de negocio:
no cerrado admite fechas coherentes, no se agregan acciones a planes
cerrados. Estadísticas para el panel y el centro de alertas.

### `reporte_service.py`
- `dashboard`: KPIs (activos, evaluaciones del periodo, HiPo, revisiones
  pendientes), distribución por clasificación, **promedio por área** (nulo si
  el área no tiene puntuaciones válidas — fix anti división por cero), estado
  de revisiones, top-10 HiPo y evolución de promedios por periodo.
- `matriz_nueve_box`: desempeño (promedio de factores tipo desempeño × 100)
  vs potencial (puntuación global); cortes por **terciles de la población**
  (p33/p67) → 9 cajas con etiquetas de sucesión ("Estrellas", "Enigmas"…).
- `comparar_colaboradores`: mediciones VÁLIDAS de 2-6 colaboradores
  normalizadas min-max 0-100 **entre los comparados** + su evaluación del
  periodo (alimenta el radar del frontend).
- `exportar_evaluaciones_csv` y `exportar_evaluaciones_xlsx`: exportación CSV o
  Excel formateado con todos los campos de resultado (permiso
  `reportes.exportar` en el router).
- `alertas`: pendientes operativos del último periodo (revisiones sin hacer,
  mediciones PENDIENTE/INVALIDA, planes en riesgo/vencidos, resultados sin
  explicación).

### `ia_service.py`
Integración Azure OpenAI con **degradación elegante**: si no hay credenciales
(o falla la llamada con timeout configurable) genera una explicación
**determinista local** y marca el origen (`azure_openai` /
`local_determinista`). `consulta_asistida` responde preguntas con el contexto
autorizado y, sin IA, devuelve guía genérica + advertencia. El *prompt* de
sistema restringe: solo datos del contexto, sin inventar, decisión final
humana.

### `auditoria_service.py`
`registrar` agrega el registro (sin confirmar transacción: la confirma el
caso de uso); `consultar` filtra/pagina por acción o texto.


## 8. Backend — `routers/` (API HTTP)

Todos montados bajo `/api`. Cada endpoint declara su permiso con
`Depends(require_permission("..."))`; los errores de negocio se traducen a
códigos HTTP (404 no existe, 409 duplicado, 422 regla de negocio, 403 permisos).

| Router | Endpoints principales | Permisos |
|---|---|---|
| `auth` | `POST /auth/login`, `GET /auth/me` | público / autenticado |
| `usuarios` | `GET/POST /usuarios`, `PUT /usuarios/{id}`, `GET /usuarios/roles` | `usuarios.gestionar` |
| `colaboradores` | `GET/POST /colaboradores`, `GET/PUT/DELETE /colaboradores/{id}`, `GET .../perfil`, `GET .../historial`, `GET .../planes`, `POST .../observaciones` | `colaboradores.consultar` / `gestionar` |
| `indicadores` | `GET/POST /indicadores`, `PUT /indicadores/{id}`, `GET /periodos`, `GET/POST /mediciones`, `GET /plantilla-csv`, `POST /carga-csv`, `PATCH /mediciones/{id}/validez` | `colaboradores.consultar` / `indicadores.gestionar` |
| `evaluaciones` | `POST /evaluaciones/ejecutar`, `GET /evaluaciones`, `GET /evaluaciones/{id}`, `POST .../explicacion`, `POST .../observaciones` | `evaluaciones.ejecutar`, `reportes.consultar`, `ia.usar`, `evaluaciones.revisar` |
| `revisiones` | `POST /revisiones/resultados/{resultado_id}` | `evaluaciones.revisar` |
| `reportes` | `GET /dashboard`, `GET /matriz-9box`, `GET /comparar?ids=`, `GET /alertas`, `GET /export/evaluaciones.csv`, `GET /export/evaluaciones.xlsx`, `GET /config` | `reportes.consultar` / `reportes.exportar` |
| `configuracion` | `GET/PUT /configuracion/areas-pruebas`, `GET /configuracion`, `GET /configuracion/activa`, `POST /configuracion`, `POST /configuracion/{id}/activar` | `configuracion.gestionar` |
| `planes` | `GET/POST /planes`, `GET /planes/estadisticas`, `GET/PUT/DELETE /planes/{id}`, `POST /planes/{id}/acciones`, `PATCH /planes/acciones/{accion_id}` | `planes.consultar` / `planes.gestionar` |
| `auditoria` | `GET /auditoria` | `auditoria.consultar` |
| `ia` | `POST /ia/consulta` | `ia.usar` |

Los routers delegan en los servicios y se limitan a: validar la entrada con
`schemas/`, resolver permisos, traducir errores y dar formato a la respuesta.

## 9. Frontend — cómo está construido

### Punto de entrada y rutas
- `main.jsx`: monta `<App/>` dentro de `HashRouter` (rutas con `#/`, ideal para
  nginx sin configurar history) y `AuthProvider`.
- `App.jsx`: define las rutas; el componente `RutaProtegida` exige sesión y
  permiso (`puede('...')`); sin sesión redirige a `/login`.

### Sesión y HTTP
- `context/AuthContext.jsx`: guarda el usuario (con permisos) en estado y
  `localStorage`; expone `iniciarSesion`, `cerrarSesion` y `puede(permiso)`.
- `api/client.js`: `fetch` centralizado que inyecta `Authorization: Bearer`,
  convierte errores FastAPI a mensajes legibles, redirige a login si llega
  `401` (sesión expirada) y `descargarCsv` descarga blobs (plantilla y
  exportaciones).
- En desarrollo, Vite hace **proxy** de `/api` → `http://localhost:8000`
  (`vite.config.js`); en Docker lo hace nginx.

### Navegación y alertas
- `components/Layout.jsx`: sidebar con menú filtrado por permisos del rol,
  barra superior con nombre/rol, cierre de sesión y la **campana del centro
  de alertas** (`GET /api/reportes/alertas` cada 2 minutos) con panel
  desplegable de pendientes.

### Páginas (un archivo por módulo)

| Página | Qué hace | Endpoint base |
|---|---|---|
| `Login.jsx` | Formulario de acceso; si ya hay sesión redirige con `<Navigate>`. | `/auth/login` |
| `Dashboard.jsx` | KPIs, distribución por clasificación, gráfica SVG de evolución por periodo, promedios por área, top HiPo y export CSV. | `/reportes/dashboard` |
| `Colaboradores.jsx` | Búsqueda/filtros paginados; crear/editar/desactivar (según permiso). | `/colaboradores` |
| `ColaboradorDetalle.jsx` | Perfil consolidado: datos, mediciones por periodo, histórico de evaluaciones, planes y observaciones (puede agregar). | `/colaboradores/{id}/perfil` |
| `Evaluaciones.jsx` | Listado con filtros + botón **Ejecutar evaluación** por periodo (modal) y resumen de la ejecución. | `/evaluaciones` |
| `EvaluacionDetalle.jsx` | Factores con barras de contribución, explicación (regenerable con IA), revisiones humanas y observaciones. | `/evaluaciones/{id}` |
| `MatrizSucesion.jsx` | Cuadrícula 9-box interactiva (desempeño × potencial) con detalle por cuadrante. | `/reportes/matriz-9box` |
| `Comparador.jsx` | Selección de 2-6 colaboradores, **radar SVG** de indicadores normalizados y tabla comparativa. | `/reportes/comparar` |
| `Indicadores.jsx` | Catálogo de indicadores, mediciones por colaborador/periodo y validación de calidad. | `/indicadores` |
| `CargaDatos.jsx` | Carga masiva CSV: drag&drop, plantilla descargable, editor, "solo validar" o "validar y registrar" y reporte de rechazos. | `/indicadores/carga-csv` |
| `Planes.jsx` | CRUD de planes y acciones, marcar acciones (recalcula avance), estados y riesgo. | `/planes` |
| `Configuracion.jsx` | Pruebas por área; versiones de criterios, pesos, umbral y cobertura. | `/configuracion` |
| `Usuarios.jsx` | Gestión de usuarios y consulta de roles/permisos. | `/usuarios` |
| `Auditoria.jsx` | Registro de auditoría filtrable y paginado. | `/auditoria` |


## 10. El pipeline HiPo paso a paso (ejemplo numérico)

Súper simplificado con 3 colaboradores y 2 indicadores (pesos 0.6/0.4,
umbral HiPo = 75):

```
Mediciones válidas 2026-S1:        LIDERAZGO  DESEMPENO_GLOBAL
  Ana   (COL-001)                     90          80
  Beto  (COL-002)                     60          70
  Carla (COL-003)                     30          40

1) Normalización min-max (0..1):
   LIDERAZGO:           Ana 1.0 | Beto 0.5 | Carla 0.0
   DESEMPENO_GLOBAL:    Ana 1.0 | Beto 0.6 | Carla 0.0

2) Puntuación = 100 × (0.6×normL + 0.4×normD) / 1.0:
   Ana   = 100 × (0.6 + 0.4) = 100.0  → ≥ 75 → ALTO_POTENCIAL
   Beto  = 100 × (0.30 + 0.24) = 54.0 → ESTANDAR (o EN_DESARROLLO si ≥ 0.85×75)
   Carla = 0.0                → ESTANDAR (cobertura 2/2 → COMPLETA)

3) Si Carla solo tuviera LIDERAZGO: cobertura 1/2 = 0.5 < 0.8 → INCOMPLETA,
   y con 0 mediciones válidas → NO_EVALUABLE (RN-02).

4) Cada factor guarda {valor, normalizado, peso, contribución} →
   "factores principales" que alimentan la explicación IA y la UI.
```

## 11. Infraestructura y despliegue

### `docker-compose.yml` (3 servicios)
- **db**: PostgreSQL 16 con volumen persistente y healthcheck (`pg_isready`).
- **backend**: construye `backend/Dockerfile` (python:3.12-slim), aplica
  `alembic upgrade head`, espera a que db esté *healthy* y no publica el puerto
  al host. Requiere secretos y ejecuta sin datos demo.
- **frontend**: build multi-stage (node:20 compila con Vite → nginx:alpine
  sirve `dist/`). `nginx.conf` sirve la SPA (`try_files … /index.html` por el
  HashRouter) y hace **proxy** de `/api/` → `backend:8000`. Publica en
  `127.0.0.1:8081` por defecto.

Arranque: sustituye secretos en `.env.example`, cópialo a `.env` y ejecuta
`docker compose up --build -d`. La interfaz queda en `http://127.0.0.1:8081`;
para acceso remoto se requiere un proxy inverso con TLS.

### CI (`.github/workflows/ci.yml`)
- Job **backend**: instala requirements, valida la migración desde una base SQLite
  limpia y corre `pytest`.
- Job **frontend**: `npm ci` + `npm run build`.

## 12. Cómo ejecutar y verificar

```powershell
# --- Desarrollo local ---
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
# → BD SQLite talento.db + datos demo en el primer arranque

cd frontend
npm ci
npm run dev      # http://localhost:5173 (proxy /api → 8000)

# --- Pruebas y verificaciones ---
cd backend
venv\Scripts\python -m pytest tests -q
venv\Scripts\python verificar_modulos_e2e.py           # 11 modulos en vivo
venv\Scripts\python verificar_vivo.py                # stack Docker (8081)
venv\Scripts\python smoke_e2e.py                       # (servidor en 8001)

# --- Docker ---
docker compose up --build
```

En Compose, reemplaza primero los valores de `.env.example`; el despliegue usa
PostgreSQL, no publica directamente la API y no crea usuarios ni datos demo. Las
cuentas demo (`Admin123!`, `Gestor123!`, `Evaluador123!`, `Consulta123!`) son
exclusivas del entorno local de desarrollo.

## 13. Reglas de negocio y dónde se implementan

| Regla | Descripción | Implementación |
|---|---|---|
| RN-01 | Solo mediciones VALIDA participan; recargar un valor lo regresa a PENDIENTE | `evaluacion_service` (filtro `Validez.VALIDA`), `indicador_service` (upsert) |
| RN-02 | Cobertura insuficiente → INCOMPLETA / NO_EVALUABLE, nunca equivalente a completa | `evaluacion_service` (comparación con `cobertura_minima`), modelo `EstadoEvaluacion` |
| RN-03 | Criterios versionados, una sola versión activa | `configuracion_service`, `ConfiguracionEvaluacion.activa` |
| RN-04/05 | Histórico por periodo sin sobrescribir | cada ejecución crea `Evaluacion` nueva; `historial_colaborador` |
| RN-06 | Revisión humana explícita de resultados | `revision_service`, `RevisionHumana`, centro de alertas |
| RN-07 | Exportación restringida por permiso | `reportes.py` (`reportes.exportar`) |
| RN-08 | Trazabilidad de operaciones | `auditoria_service` invocado desde todos los servicios |

## 14. Decisiones de diseño destacadas

- **Permisos vigentes siempre**: el JWT incluye permisos, pero cada petición
  los recarga desde la BD → cambiar el rol de un usuario aplica al instante.
- **Degradación elegante de IA**: el sistema es 100 % funcional sin Azure
  OpenAI (explicaciones deterministas locales con origen marcado).
- **IA con contexto mínimo**: la IA nunca recibe datos crudos; solo resúmenes
  autorizados construidos por el servidor (privacidad por diseño).
- **Alembic en producción** y seed idempotente: los cambios del esquema se
  versionan; los ajustes de datos iniciales no duplican registros.
- **Baja lógica de colaboradores**: se conserva todo el histórico.
- **`MODELO_VERSION`**: la puntuación está aislada en `evaluacion_service`
  y versionada → lista para sustituirse por Azure ML sin tocar el resto.
