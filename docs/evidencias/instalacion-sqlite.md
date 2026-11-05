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
