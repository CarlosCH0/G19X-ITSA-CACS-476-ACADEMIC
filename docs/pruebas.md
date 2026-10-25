# Ejecución de pruebas

## Backend

Desde `backend/`, instala las dependencias y ejecuta toda la suite:

```powershell
python -m pip install -r requirements.txt
python -m pytest tests -q
```

Para ejecutar una prueba puntual:

```powershell
python -m pytest tests/test_health.py -q
python -m pytest tests/test_planes.py -q
```

## Frontend

Desde `frontend/`, instala dependencias, ejecuta las pruebas de utilidades y genera
la compilación de producción:

```powershell
npm ci
npm test
npm run build
```
