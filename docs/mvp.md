
# Explicación del MVP — Sistema de Identificación de Alto Potencial


## 1. ¿Qué problema resuelve el proyecto?

Imagínate una empresa con muchos trabajadores. Cuando se abre un puesto importante
o se quiere decidir en quién invertir (capacitaciones, promociones, etc.), la
pregunta siempre es la misma: **¿quién tiene más potencial?**

Antes esto se hacía "a ojo": dependía de la memoria o la opinión del jefe. El
proyecto lo que hace es **usar datos reales** (desempeño, liderazgo, cursos
aprobados, cumplimiento de objetivos, etc.) para calcular una **puntuación** y
conocer qué trabajadores son de **alto potencial**. A esas personas en el
proyecto las llamamos **HiPo** (viene del inglés *High Potential*).

La regla más importante del proyecto es esta:

> **El sistema no decide solo.** Calcula y propone, pero siempre hace falta que
> una persona autorizada revise y confirme el resultado. El sistema es una ayuda,
> no el jefe.


---

## 2. ¿Qué es un "MVP" y por qué se hizo uno?

MVP significa **Producto Mínimo Viable** (*Minimum Viable Product*). Es como
hacer el "borrador funcional" de un producto: **la versión más pequeña que ya
sirve y demuestra que la idea funciona**, sin gastar tiempo en lujos que pueden
esperar.

Una analogía: si te encargan construir un coche, el MVP no es un coche sin
llantas. Es algo más simple, como una bicicleta con motor: te lleva de un lugar
a otro (resuelve el problema de transporte) y te permite aprender qué mejorar
antes de construir el coche completo.

En este proyecto, el MVP sirve para **comprobar la idea central**: que se puede
identificar talento de alto potencial con datos, de forma trazable (que se pueda
saber *por qué* salió cada resultado) y con revisión humana obligatoria.


---

## 3. ¿Qué puede hacer el MVP y qué no?

| ✅ Sí lo hace (alcance del MVP) | ❌ No lo hace (eso va en el producto completo) |
|---|---|
| Iniciar sesión con usuario y contraseña (JWT) | Cargar datos masivos desde archivos CSV |
| Control de acceso con 4 roles y 10 permisos | Matriz de sucesión 9-box |
| Administrar colaboradores (crear, editar, ver su perfil e histórico) | Comparador de periodos con gráfica radar |
| Administrar indicadores y cargar mediciones por periodo | Planes de desarrollo para cada persona |
| Configurar los criterios de evaluación (por versiones) | Centro de alertas con campanita de notificaciones |
| Ejecutar la evaluación y clasificar a la gente (el "pipeline" HiPo) | Inteligencia artificial (Azure OpenAI) |
| Revisión humana de cada resultado, con observaciones | |
| Dashboard (panel de control) y exportar a CSV | |
| Registro de auditoría (quién hizo qué y cuándo) | |
| Todo corre en Docker y tiene pruebas automáticas (CI) | |

**En resumen:** el MVP tiene el "corazón" del producto (cargar datos → evaluar →
revisar → consultar) y deja fuera las funciones "extra" que vienen después.

---

## 4. ¿Cómo está organizado por dentro?

El MVP tiene tres partes que trabajan juntas. Una analogía fácil: **un
restaurante**.

| Parte | Qué es | Analogía con el restaurante |
|---|---|---|
| **Frontend** (`frontend/`) | La página web que ve el usuario. Hecha con **React 18 + Vite** | El comedor: las mesas, el menú, donde el cliente pide |
| **Backend** (`backend/`) | El "cerebro" que calcula todo. Hecho con **Python + FastAPI** | La cocina: ahí se prepara la comida de verdad |
| **Base de datos** | Donde se guarda todo. **PostgreSQL** en Docker (o **SQLite** al desarrollar en la compu) | La despensa: guarda los ingredientes y las recetas |

Cuando haces clic en un botón de la página, el frontend le manda un mensaje al
backend (a través de lo que se llama una **API**), el backend hace los cálculos
consultando la base de datos y le responde al frontend para mostrarte el
resultado. El "idioma" que usan entre ellos es JSON, que es básicamente texto
organizado.

Además hay dos ayudas más:

- **Docker Compose**: levanta todo el sistema (base de datos + backend +
  frontend) con **un solo comando**, sin instalar nada a mano.
- **GitHub Actions (CI)**: cada vez que se sube código, corre las pruebas del
  backend y compila el frontend automáticamente, para asegurarse de que nada se
  rompió.

### Carpetas importantes del backend

```
backend/
├── app/
│   ├── main.py          ← aquí arranca la API
│   ├── core/            ← configuración y seguridad (contraseñas, tokens)
│   ├── db/              ← conexión a la base de datos y datos de ejemplo
│   ├── models/          ← las "tablas" de la base de datos (qué se guarda)
│   ├── routers/         ← las direcciones (URLs) de la API
│   ├── schemas/         ← la forma de los datos que entran y salen
│   └── services/        ← la lógica de negocio (aquí está el cálculo importante)
├── tests/               ← las pruebas automáticas (pytest)
└── verificar_mvp.py     ← verificación completa de los 8 módulos del MVP
```

---

## 5. Los tipos de usuarios (roles)

No todos pueden hacer lo mismo. Hay **4 roles** con **10 permisos** distintos:

| Rol | ¿Quién es? | ¿Qué puede hacer? |
|---|---|---|
| **ADMINISTRADOR** | El que administra el sistema | Todo: usuarios, roles, datos, evaluaciones, reportes y auditoría |
| **GESTOR_TALENTO** | Alguien de Recursos Humanos / talento | Gestionar colaboradores e indicadores, ejecutar y revisar evaluaciones, configurar criterios, ver y exportar reportes |
| **EVALUADOR** | El que revisa resultados | Ver colaboradores y reportes, ejecutar evaluaciones y **revisar los resultados** |
| **CONSULTA** | Solo quiere ver información | Ver colaboradores y reportes. Nada más |

Por ejemplo: si un usuario **CONSULTA** intenta exportar el CSV o entrar a la
auditoría, el sistema le responde con un error 403 ("no tienes permiso"). Eso
está comprobado en las pruebas.

---

## 6. El corazón del MVP: ¿cómo se calcula quién es HiPo?

Esta es la parte más importante. El sistema la hace en automático cuando
alguien ejecuta una evaluación. Voy a explicarla paso a paso.

### Paso 0: Los indicadores

Primero hay que saber **qué se mide**. El sistema trae 11 indicadores base,
cada uno con un "peso" (qué tanto importa en la puntuación final). Los pesos
suman 1.00:

| Indicador | Tipo | Peso |
|---|---|---|
| Desempeño global | Desempeño | 0.20 |
| Liderazgo | Competencia | 0.12 |
| Cumplimiento de objetivos | Objetivo | 0.12 |
| Crecimiento de desempeño | Desempeño | 0.10 |
| Puntaje de capacitación | Capacitación | 0.10 |
| Comunicación | Competencia | 0.08 |
| Años de experiencia | Experiencia | 0.07 |
| Colaboración | Competencia | 0.06 |
| Impacto en proyectos | Organizacional | 0.06 |
| Cursos aprobados | Capacitación | 0.05 |
| Rotación del equipo | Organizacional | 0.04 |

Fíjate en el último: la **rotación del equipo** es el único donde **menos es
mejor** (si a tu equipo se le van muchas personas, eso es malo). El sistema lo
toma en cuenta invirtiendo el número.

### Paso 1: Se cargan las mediciones

Cada cierto tiempo (por ejemplo cada semestre, que en el sistema se llama
**periodo**, como "2026-S1") se cargan las mediciones de cada colaborador.
Cada medición tiene un estado de validez:

- **Válida** ✅ → el dato es confiable y **sí cuenta** para evaluar.
- **Pendiente** ⏳ → aún no se confirma.
- **Inválida** ❌ → el dato está mal y **no cuenta**.

**Solo las mediciones válidas se usan.** Así se evita clasificar a alguien con
datos chuecos.

### Paso 2: Normalizar (poner a todos en la misma escala)

Problema: no se puede comparar "años de experiencia" con "puntaje de
capacitación" directamente, porque miden cosas distintas y en escalas distintas.

Solución: la **normalización min-max**. Se busca el valor más bajo y el más
alto de cada indicador **dentro del grupo evaluado**, y a cada persona se le
asigna un número entre 0 y 1 según dónde quedó:

```
normalizado = (valor de la persona - el más bajo del grupo) / (el más alto - el más bajo)
```

Ejemplo con calificaciones de un examen: si la nota más baja del grupo fue 40 y
la más alta 90, alguien con 65 queda en (65−40)/(90−40) = **0.5**, o sea, a la
mitad del grupo. Así todos los indicadores quedan en la misma escala (de 0 a 1)
y ya se pueden comparar.

Detalle curioso: si en un indicador **todos tienen el mismo valor**, se les da
0.5 a todos (contribución neutra, porque nadie destaca sobre nadie).

### Paso 3: Puntuación ponderada

Ahora sí se calcula la nota final. Cada indicador aporta según su peso:

```
puntuación = 100 × (suma de: peso × valor normalizado) / (suma de los pesos usados)
```

El resultado va de **0 a 100**.

### Paso 4: La cobertura (¿tiene suficientes datos?)

Antes de clasificar, el sistema revisa la **cobertura**: qué porcentaje de los
indicadores tienen datos válidos.

- Si la cobertura es **80% o más** → la evaluación está **completa**.
- Si es **menos del 80%** → hay información insuficiente y la persona se marca
  como **NO EVALUABLE**. Esto es a propósito: alguien con pocos datos **no debe
  aparecer como si tuviera una evaluación completa**.

### Paso 5: La clasificación

Con la puntuación y la cobertura, cada persona queda en una de 4 categorías:

| Categoría | Cuándo | Significado |
|---|---|---|
| **ALTO_POTENCIAL (HiPo)** | Puntuación ≥ 75 | Talento de alto potencial |
| **EN_DESARROLLO** | Puntuación ≥ 63.75 (o sea, 75 × 0.85) y menor a 75 | Está cerca: hay que desarrollarla |
| **ESTANDAR** | Puntuación menor a 63.75 | Evaluación normal |
| **NO_EVALUABLE** | Cobertura menor a 80% | Faltan datos, no se puede clasificar |

Los números 75 y 0.85 no son mágicos: son la **configuración versión 1** y se
pueden cambiar creando una nueva versión (ver paso 9).

### Paso 6: Trazabilidad (¿por qué me salió esa nota?)

El sistema guarda, para cada persona evaluada, **la lista de factores**: qué
indicador contribuyó y cuánto aportó a la puntuación. También genera una
**explicación en texto** (por ahora con una fórmula fija, sin inteligencia
artificial). Gracias a eso, si alguien pregunta "¿por qué esta persona salió
HiPo?", la respuesta está ahí, con números.

### Paso 7: Revisión humana

Cada resultado empieza como **pendiente**. Un usuario con permiso (por ejemplo
un EVALUADOR) lo revisa y puede:

- **Confirmarlo** (si está de acuerdo), o
- Dejarlo **pendiente**, y escribir una **observación** explicando el motivo.

Sin este paso, el resultado no cuenta como validado.

### Paso 8: Auditoría e histórico

- **Auditoría**: casi todo queda registrado en un historial: quién hizo qué,
  cuándo y con qué datos. Sirve para que nada sea un misterio.
- **Histórico**: cada vez que se ejecuta una evaluación, **se agrega un registro
  nuevo, nunca se borra el anterior**. Así se puede ver la evolución de cada
  persona entre periodos.

### Paso 9: La configuración versionada

Los criterios (pesos, umbral HiPo, cobertura mínima) se guardan **por
versiones**. Solo puede haber **una versión activa** a la vez. Si el equipo de
talento decide que el liderazgo importa más, crea una versión nueva, y la
anterior queda guardada con sus resultados. Así, los resultados viejos siempre
se pueden explicar con los criterios de su época.

---

## 7. Un ejemplo completo (con números fáciles)

Para que se entienda, imaginemos un grupo pequeño donde solo usamos **2
indicadores**: Desempeño (peso 0.6) y Liderazgo (peso 0.4). *(En el sistema real
son los 11 de la tabla anterior; esto es solo para simplificar.)*

**Paso 2 — Normalizar** (se toma el mínimo y el máximo de cada columna):

| Persona | Desempeño | Liderazgo | Desempeño normalizado | Liderazgo normalizado |
|---|---|---|---|---|
| Ana | 95 | 90 | (95−45)/50 = **1.0** | (90−60)/30 = **1.0** |
| Beto | 80 | 81 | (80−45)/50 = **0.7** | (81−60)/30 = **0.7** |
| Carla | 45 | 60 | (45−45)/50 = **0.0** | (60−60)/30 = **0.0** |
| David | 70 | *(sin dato)* | 0.5 | — |

*(En desempeño el mínimo fue 45 y el máximo 95, por eso se divide entre 50.
En liderazgo el mínimo fue 60 y el máximo 90, por eso se divide entre 30.)*

**Pasos 3 y 5 — Puntuación y clasificación:**

- **Ana** = 100 × (0.6×1.0 + 0.4×1.0) = **100 puntos** → es mayor o igual a 75
  → **ALTO POTENCIAL (HiPo)**
- **Beto** = 100 × (0.6×0.7 + 0.4×0.7) = **70 puntos** → está entre 63.75 y 75
  → **EN DESARROLLO**
- **Carla** = 100 × (0.6×0.0 + 0.4×0.0) = **0 puntos** → **ESTANDAR**
- **David** solo tiene 1 de 2 indicadores → cobertura 50%, que es menos del 80%
  → **NO EVALUABLE** (aunque se pueda calcular una puntuación, falta
  información para confiar en el resultado)

Y de Ana se guardaría su lista de factores: "Desempeño (0.6×1.0 = 0.60) y
Liderazgo (0.4×1.0 = 0.40)", para que cualquiera vea por qué salió HiPo.
Después, un evaluador tendría que **confirmar** ese resultado para que quede
validado.

---

## 8. Las pantallas que tiene el frontend

| Pantalla | Para qué sirve |
|---|---|
| **Login** | Iniciar sesión con correo y contraseña |
| **Dashboard** | Panel principal: cuántos colaboradores activos hay, cuántos HiPo, cuántas revisiones pendientes, promedios por área, top 10 de HiPo y evolución por periodo |
| **Colaboradores** | Lista con búsqueda, y crear/editar colaboradores |
| **Detalle de colaborador** | Perfil completo: sus mediciones, su histórico de evaluaciones y observaciones |
| **Evaluaciones** | Lista de evaluaciones con filtros (periodo, clasificación, área) y botón para ejecutar una evaluación |
| **Detalle de evaluación** | La puntuación, la clasificación, los factores, la explicación y el botón para confirmar la revisión |
| **Indicadores** | Catálogo de indicadores y carga de mediciones (incluso varias a la vez) |
| **Configuración** | Crear nuevas versiones de criterios (pesos y umbrales) |
| **Auditoría** | El historial de acciones del sistema |
| **Usuarios** | Administrar usuarios y sus roles |

Cada pantalla solo aparece si tu rol tiene el permiso correspondiente. Si no lo
tiene, la página le avisa al usuario que no puede entrar a esa sección.

---

## 9. Los datos y usuarios de ejemplo

El MVP trae **datos de demostración** que se cargan solos la primera vez que
arranca (mientras `SEED_DEMO_DATA=true`):

- **12 colaboradores** de ejemplo.
- **2 periodos** de mediciones (2025-S2 y 2026-S1), con una mezcla de datos
  válidos, pendientes e inválidos (para comprobar que el sistema los filtra
  bien).
- El colaborador **COL-012** tiene pocos datos en 2026-S1 a propósito, para
  demostrar el caso **NO_EVALUABLE**.
- La configuración de criterios **versión 1**, ya activa.

**Usuarios de prueba:**

| Usuario | Contraseña | Rol |
|---|---|---|
| admin@develop.com.mx | Admin123! | ADMINISTRADOR |
| gestor@develop.com.mx | Gestor123! | GESTOR_TALENTO |
| evaluador@develop.com.mx | Evaluador123! | EVALUADOR |
| consulta@develop.com.mx | Consulta123! | CONSULTA |

---


## 10. ¿Cómo sabemos que funciona bien?

El MVP se revisa de tres formas:

1. **16 pruebas automáticas con pytest** (`backend/tests/`): prueban el login y
   los roles, la administración de datos, el cálculo de evaluaciones y los
   reportes. Por ejemplo: hay una prueba que verifica que si vuelves a ejecutar
   una evaluación **el histórico no se borra**, y otra que comprueba que
   COL-012 sale NO_EVALUABLE.
2. **Verificación de punta a punta** (`verificar_mvp.py`): levanta el servidor
   de verdad y prueba los **8 módulos** completos en orden: salud del servicio →
   login y roles → colaboradores → mediciones → configuración → evaluación +
   revisión humana → reportes y CSV → auditoría.
3. **Integración continua (GitHub Actions)**: cada vez que se sube código, se
   ejecutan las pruebas del backend y se compila el frontend en la nube. Si algo
   falla, se entera uno al instante.

---

## 12. ¿Qué se quiere aprender con este MVP?

Un MVP no se hace solo por hacer: se hace para **aprender**. Con este queremos
responder tres preguntas:

1. ¿Los criterios y umbrales que vienen por defecto (umbral 75, cobertura 80%)
   **clasifican el talento de forma razonable**?
2. ¿El flujo de trabajo (cargar datos → evaluar → revisar → consultar) **encaja
   con cómo trabaja el negocio** o resulta pesado?
3. ¿La trazabilidad (los factores + la auditoría) **les da suficiente
   confianza** a las personas que revisan?

Con esas respuestas, el producto completo agrega lo que falta: carga masiva
CSV, matriz 9-box, comparador de periodos, planes de desarrollo y alertas.

---

## 12. Resumen en pocas palabras

> El MVP es una página web pequeña pero completa donde una empresa carga los
> datos de desempeño de sus trabajadores, el sistema los acomoda en la misma
> escala, calcula una puntuación de 0 a 100 y dice quién parece tener alto
> potencial (HiPo), quién está en desarrollo y quién no se puede evaluar por
> falta de datos. Cada resultado muestra **por qué** salió así, una persona
> siempre lo tiene que **revisar y confirmar**, todo queda **registrado** en la
> auditoría, y nada se borra: el histórico se conserva. Con eso se comprueba que
> la idea del producto funciona antes de construir la versión grande.
