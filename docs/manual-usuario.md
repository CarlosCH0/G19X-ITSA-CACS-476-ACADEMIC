# Manual de Usuario — Sistema de Identificación de Talento de Alto Potencial

PLURIONE S.A. DE C.V.

Develop Talent & Technology

MANUAL DE USUARIO

Sistema de Identificación de Talento de Alto Potencial (Talento HiPo) — v1.1

### 1. ¿Para qué sirve este sistema?

Talento HiPo es una página web que ayuda a la empresa a descubrir a las personas con mayor potencial. El sistema reúne la información de cada persona —su desempeño, sus competencias, sus cursos, su experiencia y el cumplimiento de sus objetivos— y le da una puntuación del 0 al 100.

Con esa puntuación, el sistema clasifica a cada persona en una categoría:

| Categoría | Qué significa |
|---|---|
| Alto potencial (HiPo) | Obtuvo una puntuación alta. Es candidata para puestos de mayor responsabilidad. |
| En desarrollo | Está cerca del nivel alto. Vale la pena apoyar su crecimiento. |
| Estándar | Va bien en su puesto actual. |
| No evaluable | Le faltaron datos completos para poder evaluarla. |

Importante: el sistema no decide solo. Toda evaluación debe ser revisada y confirmada por una persona antes de que se use para tomar decisiones.

### 2. Lo que necesita para empezar

Una computadora con internet y un navegador (Chrome, Edge o Firefox).

La dirección del sistema, entregada por la empresa: http://localhost:8081/#/ (instalación local) o la que le indique su área de sistemas.

Su usuario (correo) y su contraseña.

Si aún no tiene usuario, pídalo al administrador del sistema. Las siguientes cuentas
solo existen en la instalación local de demostración y no funcionan en producción:

| Correo | Contraseña | Tipo de usuario |
|---|---|---|
| admin@develop.com.mx | Admin123! | Administrador |
| gestor@develop.com.mx | Gestor123! | Gestor de talento |
| evaluador@develop.com.mx | Evaluador123! | Evaluador |
| consulta@develop.com.mx | Consulta123! | Consulta (solo ver) |

### 3. Cómo entrar al sistema

Abra el navegador (por ejemplo Chrome).

Escriba la dirección del sistema en la barra de direcciones y presione Enter.

Escriba su correo y su contraseña.

Haga clic en el botón para entrar.

Listo: verá el Panel de talento con el resumen general.

Por seguridad, la sesión dura 8 horas. Si se cierra, solo vuelva a entrar.

Si olvidó su contraseña, pida ayuda al administrador del sistema.

Para salir, haga clic en «Cerrar sesión», arriba a la derecha.

### 4. Conozca la pantalla

Al entrar verá dos zonas: el menú, a la izquierda, y la barra superior.

### 4.1 El menú de la izquierda

Cada persona ve en el menú solo lo que le corresponde según su tipo de usuario. Para ir a cualquier sección, haga clic en su nombre:

| Opción del menú | Para qué sirve |
|---|---|
| Panel de control | Ver el resumen general: cuántas personas hay, cuántas evaluaciones, cuántos HiPo y cuántas revisiones pendientes. |
| Colaboradores | Ver y dar de alta a las personas del equipo. Al hacer clic en un nombre se abre su perfil completo. |
| Evaluaciones | Ejecutar una evaluación del periodo y ver los resultados. |
| Matriz 9-box | Ver el tablero de sucesión: quién tiene mejor desempeño y más potencial. |
| Comparador | Comparar de 2 a 6 personas lado a lado, con gráfica de radar. |
| Indicadores | Capturar las mediciones (calificaciones) de cada persona, una por una o en grupo. |
| Carga masiva | Subir muchas mediciones de una sola vez con un archivo. |
| Planes y sucesión | Crear y dar seguimiento a los planes de desarrollo de cada persona. |
| Criterios | Ajustar los pesos y el nivel mínimo para ser HiPo (solo personal autorizado). |
| Usuarios | Crear usuarios y asignar su tipo (solo administradores). |
| Auditoría | Ver el registro de quién hizo qué en el sistema (solo administradores). |

### 4.2 La barra superior

A la izquierda aparece el título «Analítica de personas».

Al centro-derecha está el botón «Alertas»: muestra los pendientes del periodo (revisiones sin confirmar, mediciones por validar, planes en riesgo). Si hay pendientes, se ve un número; si todo está en orden, dice «Todo en orden».

Después verá su nombre y su tipo de usuario.

El botón «Cerrar sesión» está al extremo derecho.

En el menú lateral también hay un interruptor de «Modo oscuro» para cambiar el color de la pantalla.

### 5. ¿Qué puede hacer cada tipo de usuario?

| Tipo de usuario | Qué puede hacer |
|---|---|
| Administrador | Todo: además de lo anterior, administra usuarios, ve la auditoría y cambia cualquier configuración. |
| Gestor de talento | El día a día completo: personas, mediciones, evaluaciones, revisión de resultados, planes y reportes. |
| Evaluador | Ejecuta evaluaciones, las revisa y confirma, y consulta reportes. |
| Consulta | Solo ver: panel, personas y reportes. No puede cambiar nada. |

Si una opción no aparece en su menú, es porque su tipo de usuario no la necesita.

### 6. El flujo de trabajo, en corto

El trabajo con el sistema sigue siempre el mismo camino:

| Paso | Qué se hace | Dónde |
|---|---|---|
| 1. Cargar datos | Capturar las mediciones de las personas del periodo | Indicadores o Carga masiva |
| 2. Validar | Marcar las mediciones como válidas (las inválidas no cuentan) | Indicadores |
| 3. Evaluar | Ejecutar la evaluación del periodo para obtener puntuaciones y categorías | Evaluaciones |
| 4. Revisar | Confirmar o dejar pendiente cada resultado, con comentarios | Evaluaciones |
| 5. Consultar | Ver paneles, matriz 9-box, comparaciones, planes y exportar información | Panel, Matriz, Comparador, Planes |

### 7. Tareas paso a paso

### 7.1 Ver el resumen general (Panel de control)

Es la primera pantalla al entrar. Muestra cuatro tarjetas —colaboradores activos, evaluaciones del periodo, personas de alto potencial y revisiones pendientes— y debajo: cuántas personas quedaron en cada categoría, la evolución del promedio por periodo, el promedio por área y el top de talento. Haga clic en cualquier nombre para abrir su perfil.

### 7.2 Registrar una persona (Colaboradores)

Entre al menú «Colaboradores».

Haga clic en el botón para agregar («Nuevo colaborador»).

Llene los datos: código, nombre completo, área, puesto y fecha de ingreso.

Guarde. La persona aparecerá en la lista y ya puede recibir mediciones.

Si una persona se va de la empresa, no se borra: se desactiva, para conservar su historial.

### 7.3 Capturar mediciones una por una o en grupo (Indicadores)

Una medición es el valor de un indicador para una persona en un periodo. Por ejemplo: el desempeño de Ana en 2026-S1.

Entre al menú «Indicadores».

Elija la persona y el periodo (por ejemplo 2026-S1).

Escriba los valores de cada indicador. Puede capturar varios de una vez.

Guarde. Las mediciones nuevas quedan como «pendientes» hasta que alguien las marca como válidas.

Revise que cada medición diga «Válida»: solo las válidas cuentan para la evaluación.

### 7.4 Subir muchas mediciones con un archivo (Carga masiva)

Entre al menú «Carga masiva».

Descargue la plantilla: es un archivo con el formato correcto y ejemplos.

Llene la plantilla con sus datos (una fila por medición) y guarde el archivo.

Vuelva a «Carga masiva», primero use «Solo validar» para revisar errores sin guardar nada.

Corrija las filas con error (el sistema le dice en qué línea está el problema) y vuelva a validar.

Cuando no haya errores, haga la carga definitiva.

### 7.5 Ejecutar una evaluación (Evaluaciones)

Entre al menú «Evaluaciones».

Elija el periodo a evaluar (por ejemplo 2026-S1).

Haga clic en «Ejecutar evaluación» y confirme.

Espere unos segundos: el sistema calcula la puntuación de cada persona y su categoría.

Haga clic en una evaluación para ver el detalle: puntuación, categoría y qué indicadores la subieron o bajaron.

### 7.6 Revisar y confirmar resultados

Esta parte es obligatoria: un resultado sin revisar no debe usarse para decidir.

Abra la evaluación y busque los resultados marcados como «Sin revisar».

Lea la puntuación, la categoría y los factores de esa persona.

Si está de acuerdo, haga clic en «Confirmar».

Si falta información o algo no cuadra, márquelo como «Pendiente» y escriba un comentario.

También puede agregar observaciones (notas) al resultado.

### 7.7 Ver el perfil completo de una persona

Entre al menú «Colaboradores».

Use el buscador para encontrar a la persona por nombre, código o área.

Haga clic en su nombre.

Verá su información, sus mediciones por periodo, sus evaluaciones y sus planes.

### 7.8 Ver la matriz de sucesión (Matriz 9-box)

Es un tablero de 9 casillas. Cada persona se coloca según dos cosas: su desempeño (de menor a mayor) y su potencial (de menor a mayor). Las personas de la casilla superior derecho son las más valiosas para la sucesión.

Entre al menú «Matriz 9-box».

Elija el periodo.

Haga clic en una casilla para ver qué personas están ahí.

### 7.9 Comparar personas (Comparador)

Entre al menú «Comparador».

Elija el periodo y seleccione de 2 a 6 personas.

Haga clic en comparar.

Verá una gráfica de radar (telaraña) y una tabla: en qué indicador destaca cada persona.

### 7.10 Planes de desarrollo (Planes y sucesión)

Un plan de desarrollo es la ruta de crecimiento de una persona: cursos, proyectos o metas con fechas. El sistema calcula el avance solo, según las acciones marcadas como terminadas.

Entre al menú «Planes y sucesión».

Haga clic en «Nuevo plan» y elija la persona, el tipo de plan (por ejemplo liderazgo), las fechas y las acciones.

Marque cada acción como terminada cuando se cumpla.

Al llegar al 100 %, el plan se cierra como completado. Si tiene acciones vencidas, el plan se marca «en riesgo» y aparece en las alertas.

### 7.11 Ajustar los criterios de evaluación (Criterios)

Solo para gestores de talento y administradores. Aquí se decide cuánto pesa cada indicador y qué puntuación mínima se necesita para ser «Alto potencial».

Entre al menú «Criterios».

Cree una nueva versión de criterios con los pesos y el umbral deseados.

Revise y active la versión nueva.

A partir de ese momento, las evaluaciones nuevas usan esa versión. Las evaluaciones pasadas no cambian.

### 7.12 Administrar usuarios (Usuarios)

Solo para administradores.

Entre al menú «Usuarios».

Haga clic en «Nuevo usuario» y escriba nombre, correo, contraseña y tipo de usuario.

Guarde. La persona ya puede entrar con ese correo y contraseña.

Para cambiar la contraseña o el tipo de usuario, edite la persona desde la lista.

### 8. El botón de alertas

El botón «Alertas» de la barra superior se actualiza solo cada 2 minutos y resume lo que falta hacer en el periodo:

Resultados sin revisión humana.

Mediciones pendientes de validar o inválidas.

Planes de desarrollo en riesgo o vencidos.

Resultados sin explicación generada.

Si no hay pendientes, el panel dice «Todo en orden: sin pendientes operativos».

### 9. Preguntas frecuentes

| Pregunta | Respuesta |
|---|---|
| Olvidé mi contraseña. | Pida ayuda al administrador del sistema; él puede asignarle una nueva. |
| No veo una opción del menú que otros sí ven. | Cada tipo de usuario ve solo lo que le corresponde. Si cree que le falta permiso, hable con el administrador. |
| Una persona salió «No evaluable». | Le faltaron mediciones válidas en el periodo. Complete y valide sus mediciones, y vuelva a ejecutar la evaluación. |
| Mis mediciones no aparecen en el resultado. | Solo cuentan las mediciones marcadas como «Válidas». Las pendientes o inválidas se quedan fuera. |
| Se cerró mi sesión sola. | Es normal: por seguridad la sesión dura 8 horas. Solo vuelva a entrar. |
| ¿Puedo borrar una evaluación? | No. El historial se conserva para que nada se pierda. Puede volver a ejecutar la evaluación y todo queda registrado. |
| Me equivoqué al cargar un archivo. | Vuelva a cargar la fila corregida: el sistema actualiza el valor y lo regresa a «pendiente» para revalidarlo. |
| ¿El sistema reemplaza la opinión del jefe? | No. Es una herramienta de apoyo; la revisión y confirmación humanas son obligatorias. |

### 10. Cuando algo no funcione

Primero intente salir del sistema y volver a entrar.

Si el problema continúa, avise al administrador del sistema (usuario ADMINISTRADOR).

El administrador puede revisar en «Auditoría» qué pasó y, si es algo técnico, escalarlo al equipo de soporte con la ayuda del Manual Técnico.

### 11. Palabras que conviene conocer

| Palabra | En palabras simples |
|---|---|
| HiPo | Persona de alto potencial (High Potential). |
| Indicador | Algo que se mide: desempeño, liderazgo, cursos, cumplimiento de objetivos, etc. |
| Medición | El valor de un indicador para una persona en un periodo. Ejemplo: desempeño 85. |
| Periodo | El lapso que se evalúa. Ejemplo: 2026-S1 (primer semestre de 2026). |
| Evaluación | El cálculo que hace el sistema con todas las mediciones del periodo. |
| Puntuación | El resultado de la evaluación, del 0 al 100. |
| Categoría | La clasificación de la persona: Alto potencial, En desarrollo, Estándar o No evaluable. |
| Revisión humana | Confirmar o rechazar un resultado. Es obligatoria antes de usarlo. |
| Matriz 9-box | Tablero de 9 casillas que cruza desempeño y potencial. |
| Plan de desarrollo | Ruta de crecimiento de una persona: cursos, proyectos y metas. |
| Auditoría | El registro de todo lo que se hace en el sistema: quién, qué y cuándo. |
