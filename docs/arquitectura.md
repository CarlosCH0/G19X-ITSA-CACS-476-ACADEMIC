# Arquitectura del sistema

## Capas del servidor

El servidor está organizado para que cada carpeta tenga una responsabilidad concreta:

| Capa | Responsabilidad |
| --- | --- |
| `core/` | Configuración, seguridad y dependencias compartidas. |
| `db/` | Motor de base de datos, sesiones y datos iniciales. |
| `models/` | Entidades persistentes de SQLAlchemy. |
| `schemas/` | Esquemas de entrada y salida de la API con Pydantic. |
| `services/` | Reglas de negocio y operaciones reutilizables. |
| `routers/` | Rutas HTTP y autorización por permisos. |
| `tests/` | Pruebas automatizadas del comportamiento de la API. |

## Flujo de una petición

1. La ruta recibe y valida la petición mediante un esquema.
2. Las dependencias comprueban la sesión y los permisos del usuario.
3. El servicio aplica la regla de negocio y consulta los modelos.
4. La ruta devuelve una respuesta validada y registra la operación cuando corresponde.

## Interfaz web

React se divide en páginas, componentes reutilizables, contexto de autenticación y un
cliente HTTP centralizado. `Layout.jsx` concentra la navegación común y las páginas
representan los módulos funcionales del sistema.

Páginas: panel de control, colaboradores (listado y perfil), evaluaciones (listado y
detalle), **matriz de sucesión 9-box**, **comparador con radar de indicadores**,
indicadores, **carga masiva CSV**, **planes de desarrollo y sucesión**, criterios,
usuarios, auditoría e inicio de sesión. La barra superior incluye el **centro de
alertas** (campana) que resume los pendientes operativos del periodo.

## Ejecución de evaluación

La evaluación valida los datos, normaliza indicadores, calcula la puntuación ponderada,
clasifica al colaborador y conserva el resultado histórico. La revisión humana y la
auditoría se mantienen como pasos explícitos para conservar la trazabilidad.

## Analítica de sucesión y desarrollo

- **Matriz 9-box** (`reporte_service.matriz_nueve_box`): desempeño (factores tipo
  desempeño) × potencial (puntuación HiPo) con cortes por terciles de la población.
- **Comparador** (`reporte_service.comparar_colaboradores`): mediciones válidas de 2-6
  colaboradores normalizadas min-max 0-100 entre los comparados.
- **Planes de desarrollo** (`plan_service`): entidades `PlanDesarrollo` y `AccionPlan`;
  el avance se recalcula al marcar acciones y los planes abiertos con acciones vencidas
  se marcan en riesgo (visibles en el centro de alertas).
- **Carga masiva CSV** (`indicador_service.cargar_mediciones_csv`): validación fila por
  fila con reporte de rechazos, modo solo-validación y upsert controlado por la regla
  RN-01 (toda recarga vuelve a PENDIENTE).

## Migraciones ligeras de datos

`db/seed.py` es idempotente y además aplica migraciones ligeras a bases ya sembradas:
`_asegurar_permisos_nuevos` incorpora permisos nuevos (p. ej. `planes.*`) a los roles
existentes y `_asegurar_planes_demo` siembra planes de ejemplo cuando la base no tiene
ninguno. Así, instalaciones previas se actualizan sin resembrar.