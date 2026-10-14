# G19X-ITSA-CACS-476-ACADEMIC

Desarrollo de Sistema de Identificación de Alto Potencial

## MVP — Sistema de Identificación de Talento de Alto Potencial

**Producto Mínimo Viable** del proyecto de desarrollo para **PluriOne S.A. de C.V. —
Develop Talent & Technology**. Es una versión independiente y autónoma: la carpeta
`proyecto/` (producto completo v1.1) no se modifica.

## ¿Qué es este MVP?

El mínimo conjunto de funcionalidades para **validar la hipótesis central del
producto**: identificar colaboradores de alto potencial de forma trazable, con
revisión humana obligatoria. Corresponde al alcance «v1.0 — Núcleo» del PRD
(prioridad Must/Should de MoSCoW).

## Alcance del MVP

| ✅ Incluido | ❌ Fuera del MVP (producto completo) |
|---|---|
| Autenticación JWT + RBAC (4 roles, 10 permisos) | Carga masiva CSV con plantilla |
| Colaboradores: CRUD, perfil consolidado, histórico | Matriz de sucesión 9-box |
| Indicadores y mediciones por periodo (bulk + validez RN-01) | Comparador con radar |
| Pipeline HiPo: normalización, puntuación, clasificación (RN-02..RN-05) | Planes de desarrollo |
| Configuración versionada de criterios (RN-03) | Centro de alertas (campana) |
| Revisión humana + observaciones (RN-06, RF-18, RF-19) | IA asistida (Azure OpenAI) |
| Dashboard, exportación CSV (RF-13, RF-14) | |
| Auditoría (RF-15, RN-08) | |
| Docker Compose + CI (GitHub Actions) | |

Cubre: RF-01..RF-06, RF-09..RF-19 y RNF-01..RNF-14.

## Arquitectura (idéntica al producto completo)

- **Backend**: Python 3.12 + FastAPI (routers → services → models con SQLAlchemy 2.x).
- **Frontend**: React 18 + Vite (SPA con HashRouter).
- **BD**: PostgreSQL en Docker (SQLite en desarrollo local).
- **Despliegue**: Docker Compose (db + backend + frontend/nginx).

## Ejecución

```powershell
# --- Desarrollo local ---
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

cd ..\frontend
npm ci
npm run dev        # http://localhost:5173 (proxy /api → 8000)

# --- Pruebas y verificación ---
cd ..\backend
venv\Scripts\python -m pytest tests -q     # 16 pruebas
venv\Scripts\python verificar_mvp.py       # E2E de los 8 módulos del MVP

# --- Docker ---
docker compose up --build
# App: http://localhost:8082 · API: http://localhost:8000/docs
```

## Usuarios de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| admin@develop.com.mx | Admin123! | ADMINISTRADOR |
| gestor@develop.com.mx | Gestor123! | GESTOR_TALENTO |
| evaluador@develop.com.mx | Evaluador123! | EVALUADOR |
| consulta@develop.com.mx | Consulta123! | CONSULTA |

Los datos demo (12 colaboradores, 2 periodos, mediciones con validez mixta y el
caso de datos insuficientes COL-012) se siembran automáticamente en el primer
arranque con `SEED_DEMO_DATA=true`.

## Ciclo operativo del MVP

1. **Cargar datos**: mediciones por colaborador/periodo (formulario bulk) y validar su calidad.
2. **Configurar** (opcional): pesos, umbral HiPo y cobertura mínima por versión.
3. **Ejecutar** la evaluación del periodo.
4. **Revisar**: confirmar o marcar pendiente cada resultado (con observaciones).
5. **Consultar**: dashboard, perfil consolidado, histórico y exportación CSV.

## Qué se quiere aprender con este MVP

- ¿Los criterios y umbrales por defecto clasifican el talento de forma razonable?
- ¿El flujo carga → evaluación → revisión cabe en el ciclo operativo del negocio?
- ¿La trazabilidad (factores + auditoría) da suficiente confianza a los revisores?

Con esas respuestas, el producto completo añade las capacidades
de escala: CSV masivo, 9-box, comparador, planes de desarrollo y alertas.
