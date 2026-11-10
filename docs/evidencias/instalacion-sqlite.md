# Evidencia de instalación limpia con SQLite

**Entorno de prueba:** Windows PowerShell, Python 3.14.2  
**Alcance:** instalación y arranque del backend siguiendo en exclusiva la sección
«Puesta en marcha (desarrollo) → Base de datos → Opción A: SQLite local» del README.

## Preparación

Se creó una copia temporal limpia del backend y del README, sin entorno virtual,
base de datos local ni archivos de caché previos. La carpeta no contenía un archivo
`.env`. La prueba no requirió Docker ni PostgreSQL.

## Instrucciones ejecutadas

Desde la raíz de la copia temporal, en PowerShell:

```powershell
cd backend
python -m venv venv
venv\Scripts\python -m pip install -r requirements.txt
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

## Resultado

- Se creó el entorno virtual y se instalaron correctamente las dependencias de
  `requirements.txt`.
- Uvicorn inició en `http://127.0.0.1:8000` y completó el arranque de la aplicación.
- `GET http://127.0.0.1:8000/api/health` respondió HTTP 200 con estado `ok` y entorno
  `desarrollo`.
- El backend creó `backend/talento.db` desde cero; la base contiene 17 tablas y los
  datos locales de demostración se inicializaron, incluidos los cuatro usuarios
  documentados para desarrollo.
- El proceso de prueba se detuvo al terminar la verificación.

## Correcciones aplicadas al README

- Se añadieron `python -m venv venv` y la instalación mediante
  `venv\Scripts\python -m pip` antes de iniciar Uvicorn, para que las instrucciones
  funcionen también en una carpeta sin entorno virtual.
- Se añadió una explicación bajo «Puesta en marcha (desarrollo)», cuyo título estaba
  seguido directamente por otro encabezado sin texto introductorio.

## Validación adicional (2026-11-09)

**Commit de referencia:** `2d81d0217abda005d580b71896b0d70c96e1ea88` (HEAD al iniciar
la validación; también se probaron los cambios locales existentes).

**Entorno:** Windows PowerShell, Python 3.14.2, Node.js 24.21.0 y npm 11.19.0.

| Comprobación | Resultado |
|---|---|
| SQLite limpia y `GET /api/health` | La API inició con una base temporal nueva y respondió HTTP 200 (`estado: ok`, `entorno: desarrollo`). |
| `npm ci` | Correcto: instaló 66 paquetes. npm informó 5 vulnerabilidades en dependencias (3 moderadas y 2 altas). |
| `npm run dev` e inicio de sesión | Vite inició en `http://127.0.0.1:5173/`; el acceso con `admin@develop.com.mx` fue correcto y cargó el panel de talento. |
| `pytest tests -q` | Correcto: 45 pruebas aprobadas; 2 advertencias deprecadas. |
| `npm test` | Correcto: 3 pruebas aprobadas, ninguna fallida. |
| `npm run build` | Correcto: Vite generó el paquete de producción. |

## Validación en clon limpio (2026-11-09)

**Commit probado:** `3e81b542e74fb4368232cb0399fd56f8f90caec9` (rama `master`).

**Entorno:** Windows PowerShell, Python 3.14.2, Node.js 24.21.0 y npm 11.19.0.

Se clonó `master` en una carpeta temporal nueva. Al iniciar, no había `.env`,
entorno virtual, base SQLite ni `node_modules`. Se siguieron las instrucciones
SQLite e interfaz web del README.

| Comprobación | Resultado |
|---|---|
| Backend y SQLite | Se creó un entorno virtual nuevo, se instalaron `requirements.txt` y Uvicorn inició. `/api/health` respondió HTTP 200 (`estado: ok`, `entorno: desarrollo`); SQLite se creó desde cero. |
| `npm ci` y `npm run dev` | Instalación correcta (66 paquetes); Vite inició en `http://127.0.0.1:5174/`. npm informó 5 vulnerabilidades en dependencias (3 moderadas y 2 altas). |
| Inicio de sesión demo | Correcto con `gestor@develop.com.mx`; la interfaz mostró el rol `GESTOR_TALENTO` y cargó el panel con 12 colaboradores. |
| `pytest tests -q` | 45 passed; 2 advertencias deprecadas. |
| `npm test` | 3 passed; ninguna fallida. |
| `npm run build` | Correcto; Vite generó los assets de producción. |

## Revisión actual de dependencias y Docker (2026-11-09)

**Base:** commit `1ee7f54` más cambios locales sin publicar.
**Entorno:** Windows PowerShell, Python 3.14.2, Node.js 24.21.0, npm 11.19.0 y Docker 29.9.3.

| Comprobación | Resultado |
|---|---|
| `npm audit` | 0 vulnerabilidades tras actualizar Vite a 7.3.8, React Router a 7.18.5 y dependencias transitivas. |
| `npm test` y `npm run build` | 3 pruebas aprobadas; compilación Vite exitosa. |
| `pytest tests -q` | 45 pruebas aprobadas; 2 advertencias deprecadas. |
| Compose normal | PostgreSQL y API sin puertos publicados; interfaz enlazada solo a `127.0.0.1`; semilla demo desactivada. |
| Compose de demostración | Arranque saludable, inicio de sesión con `gestor@develop.com.mx` y 12 colaboradores; recursos temporales eliminados al terminar. |
