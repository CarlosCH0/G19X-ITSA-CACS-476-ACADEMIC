# Guía de desarrollo

## Antes de comenzar

1. Instalar Python 3.12, Node.js 20 y Docker Desktop.
2. Copiar `.env.example` como `.env` cuando se necesiten valores personalizados.
3. Crear el entorno virtual dentro de `backend/`.
4. Instalar dependencias y ejecutar las validaciones antes de entregar cambios.

## Comandos habituales

```powershell
# Servidor
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m pytest tests -q

# Interfaz web
cd ..\frontend
npm ci
npm run build
```

## Convenciones

- Mantener la lógica de negocio en `backend/app/services/`.
- Mantener los endpoints del backend en `backend/app/routers/`.
- Reutilizar el cliente de `frontend/src/api/` para llamadas HTTP.
- No subir `.env`, bases de datos locales, `node_modules`, `dist` ni logs.
- Para cambios nuevos, actualizar la documentación o las pruebas relacionadas.

## Flujo recomendado

1. Crear una rama para el cambio.
2. Implementar el cambio en la capa correspondiente.
3. Ejecutar pruebas del backend y compilación del frontend.
4. Revisar `git diff` y `git status` para confirmar que solo aparecen archivos esperados.