# Preparar y publicar en GitHub

## Contenido del repositorio

El repositorio incluye el código fuente de `backend/` y `frontend/`, las pruebas,
las migraciones Alembic, los archivos Docker, CI, documentación, logotipos y
fixtures sintéticos de demostración:

- `db/base-de-datos.sql`: base PostgreSQL sintética con nombres, mediciones y
  evaluaciones ficticios. Incluye hashes de cuentas demo; sus contraseñas son
  públicas y no se deben reutilizar.
- `carga_masiva_prueba.csv` y `carga_masiva_prueba.xlsx`: ejemplos sintéticos
  para validar la importación.

El volcado SQL es solo para demostración y no se utiliza en el despliegue normal
con Docker Compose. La carga de datos demo en producción permanece desactivada.

## No publicar

- `.env` ni variantes como `.env.local` o `.env.production`; `.env.example` es la
  única plantilla de entorno que se versiona.
- Bases de datos locales (`*.db`, `*.sqlite*`), respaldos (`*.dump`, `*.backup`,
  `backups/`) o datos del cliente.
- Dependencias y artefactos regenerables (`.venv/`, `venv/`, `node_modules/`,
  `dist/`, `coverage/`, `bin/`, `obj/`), cachés, credenciales y claves privadas.
- Archivos mayores de 100 MB: GitHub los rechaza en repositorios Git normales;
  usa Git LFS solo si hay una necesidad real y documentada.

Antes de usar un fixture con datos nuevos, confirma que sea sintético y elimina
información personal o secretos. Las cuentas `@develop.com.mx` y sus contraseñas
son exclusivamente cuentas públicas de demostración.

## Lista de verificación antes del primer push

1. Confirma que no haya secretos, datos reales ni información que no tengas
   autorización para publicar en el código, documentación, fixtures o historial.
2. Copia `.env.example` a `.env` solo para uso local; no fuerces la inclusión de
   `.env` con `git add -f`.
3. Desde la raíz del proyecto revisa el estado y la lista exacta de archivos:

   ```powershell
   git status --short
   git ls-files
   git ls-files --others --exclude-standard
   git diff --check
   ```

4. Comprueba las exclusiones de secretos y artefactos:

   ```powershell
   git check-ignore -v .env .env.local .env.production backend\talento.db frontend\node_modules
   git check-ignore .env.example
   ```

   El primer comando debe listar todos los archivos/directorios privados. El
   segundo no debe producir salida: `.env.example` sí se versiona.

5. Busca posibles credenciales antes de preparar el commit:

   ```powershell
   git grep -n -I -E "sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY"
   ```

   Revisa cada coincidencia; los hashes PBKDF2 y contraseñas documentadas de
   demostración no son secretos operativos, pero nunca deben usarse en producción.
6. Ejecuta las pruebas y builds documentados en el README, revisa los archivos
   staged con `git diff --cached --stat` y `git diff --cached` y confirma que el
   repositorio tenga una licencia acorde al uso que autorizas.

## Publicar

El repositorio local no tiene un remoto configurado. Crea el repositorio remoto
en GitHub y sigue las instrucciones que GitHub muestre para conectarlo. Revisa la
rama actual con `git branch --show-current` y, antes de publicar, confirma el
historial con `git log --oneline --all`.

No es necesario reescribir el historial por el volcado demo incluido: los datos
que contiene son ficticios y se describen como tales. Si alguna vez incorporas
secretos reales por error, revócalos primero y elimina su historial antes de
hacer público el repositorio.

## Licencia

Este proyecto se publicará como repositorio **público y sin licencia de
reutilización**. No se añade un archivo `LICENSE`: por defecto se reservan todos
los derechos de autor y no se concede permiso general para copiar, modificar,
redistribuir o usar el código. Si los titulares autorizan reutilización más
adelante, añade la licencia aprobada y actualiza esta sección.
