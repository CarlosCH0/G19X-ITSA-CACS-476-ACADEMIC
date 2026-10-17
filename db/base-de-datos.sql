-- ============================================================================
-- Sistema de Identificacion de Talento de Alto Potencial (HiPo)
-- Base de datos completa para PostgreSQL: ESTRUCTURA + DATOS DE PRUEBA
-- ----------------------------------------------------------------------------
-- Como usarlo (desde la raiz del proyecto):
--   1) Crea una base vacia:            createdb talento
--   2) Carga este script:              psql -U talento -d talento -f db/base-de-datos.sql
--   3) Configura .env con:
--        DATABASE_URL=postgresql+psycopg2://talento:talento@localhost:5432/talento
--        SEED_DEMO_DATA=false
--   4) Arranca el backend. La base ya tiene datos, por lo que la semilla
--      automatica no vuelve a ejecutarse.
--
-- Usuarios de prueba (el hash PBKDF2 queda en la tabla usuario):
--   admin@develop.com.mx     / Admin123!     (ADMINISTRADOR)
--   gestor@develop.com.mx    / Gestor123!    (GESTOR_TALENTO)
--   evaluador@develop.com.mx / Evaluador123! (EVALUADOR)
--   consulta@develop.com.mx  / Consulta123!  (CONSULTA)
--
-- Generado desde la semilla determinista del sistema (app/db/seed.py,
-- random.Random(2026)) mas una ejecucion del pipeline del periodo 2026-S1.
-- El esquema proviene de backend/schema.sql.
-- ============================================================================

BEGIN;

-- =========================== 1) ESTRUCTURA ===========================
-- Esquema PostgreSQL del Sistema HiPo.




CREATE TABLE permiso (
	id SERIAL NOT NULL,
	codigo VARCHAR(60) NOT NULL,
	descripcion VARCHAR(255) NOT NULL,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_permiso_codigo ON permiso (codigo);


CREATE TABLE rol (
	id SERIAL NOT NULL,
	nombre VARCHAR(50) NOT NULL,
	descripcion VARCHAR(255) NOT NULL,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_rol_nombre ON rol (nombre);


CREATE TABLE colaborador (
	id SERIAL NOT NULL,
	codigo VARCHAR(30) NOT NULL,
	nombre VARCHAR(160) NOT NULL,
	area VARCHAR(120) NOT NULL,
	puesto VARCHAR(120) NOT NULL,
	fecha_ingreso DATE,
	estado BOOLEAN NOT NULL,
	PRIMARY KEY (id)
);

CREATE INDEX ix_colaborador_nombre ON colaborador (nombre);

CREATE INDEX ix_colaborador_estado ON colaborador (estado);

CREATE UNIQUE INDEX ix_colaborador_codigo ON colaborador (codigo);

CREATE INDEX ix_colaborador_area ON colaborador (area);


CREATE TABLE indicador (
	id SERIAL NOT NULL,
	codigo VARCHAR(60) NOT NULL,
	nombre VARCHAR(160) NOT NULL,
	tipo VARCHAR(30) NOT NULL,
	direccion VARCHAR(20) NOT NULL,
	activo BOOLEAN NOT NULL,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_indicador_codigo ON indicador (codigo);

CREATE INDEX ix_indicador_tipo ON indicador (tipo);


CREATE TABLE area_evaluacion (
	id SERIAL NOT NULL,
	area VARCHAR(120) NOT NULL,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_area_evaluacion_area ON area_evaluacion (area);


CREATE TABLE rol_permiso (
	rol_id INTEGER NOT NULL,
	permiso_id INTEGER NOT NULL,
	PRIMARY KEY (rol_id, permiso_id),
	FOREIGN KEY(rol_id) REFERENCES rol (id),
	FOREIGN KEY(permiso_id) REFERENCES permiso (id)
);


CREATE TABLE usuario (
	id SERIAL NOT NULL,
	nombre VARCHAR(120) NOT NULL,
	correo VARCHAR(160) NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	rol_id INTEGER NOT NULL,
	estado BOOLEAN NOT NULL,
	creado_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(rol_id) REFERENCES rol (id)
);

CREATE INDEX ix_usuario_rol_id ON usuario (rol_id);

CREATE UNIQUE INDEX ix_usuario_correo ON usuario (correo);


CREATE TABLE area_indicador (
	area_evaluacion_id INTEGER NOT NULL,
	indicador_id INTEGER NOT NULL,
	PRIMARY KEY (area_evaluacion_id, indicador_id),
	FOREIGN KEY(area_evaluacion_id) REFERENCES area_evaluacion (id) ON DELETE CASCADE,
	FOREIGN KEY(indicador_id) REFERENCES indicador (id) ON DELETE CASCADE
);


CREATE TABLE medicion_indicador (
	id SERIAL NOT NULL,
	colaborador_id INTEGER NOT NULL,
	indicador_id INTEGER NOT NULL,
	periodo VARCHAR(20) NOT NULL,
	valor FLOAT NOT NULL,
	validez VARCHAR(15) NOT NULL,
	comentario VARCHAR(255) NOT NULL,
	fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_medicion_periodo UNIQUE (colaborador_id, indicador_id, periodo),
	FOREIGN KEY(colaborador_id) REFERENCES colaborador (id),
	FOREIGN KEY(indicador_id) REFERENCES indicador (id)
);

CREATE INDEX ix_medicion_indicador_validez ON medicion_indicador (validez);

CREATE INDEX ix_medicion_indicador_colaborador_id ON medicion_indicador (colaborador_id);

CREATE INDEX ix_medicion_indicador_indicador_id ON medicion_indicador (indicador_id);

CREATE INDEX ix_medicion_indicador_periodo ON medicion_indicador (periodo);


CREATE TABLE plan_desarrollo (
	id SERIAL NOT NULL,
	colaborador_id INTEGER NOT NULL,
	titulo VARCHAR(160) NOT NULL,
	objetivo TEXT NOT NULL,
	foco VARCHAR(60) NOT NULL,
	fecha_inicio DATE NOT NULL,
	fecha_fin DATE NOT NULL,
	estado VARCHAR(15) NOT NULL,
	progreso FLOAT NOT NULL,
	responsable_id INTEGER,
	creado_por_id INTEGER NOT NULL,
	fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	fecha_actualizacion TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(colaborador_id) REFERENCES colaborador (id),
	FOREIGN KEY(responsable_id) REFERENCES usuario (id),
	FOREIGN KEY(creado_por_id) REFERENCES usuario (id)
);

CREATE INDEX ix_plan_desarrollo_estado ON plan_desarrollo (estado);

CREATE INDEX ix_plan_desarrollo_colaborador_id ON plan_desarrollo (colaborador_id);


CREATE TABLE configuracion_evaluacion (
	id SERIAL NOT NULL,
	version INTEGER NOT NULL,
	nombre VARCHAR(120) NOT NULL,
	criterios JSON NOT NULL,
	reglas JSON NOT NULL,
	umbral_hipo FLOAT NOT NULL,
	activa BOOLEAN NOT NULL,
	creado_por_id INTEGER NOT NULL,
	fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(creado_por_id) REFERENCES usuario (id)
);

CREATE UNIQUE INDEX ix_configuracion_evaluacion_version ON configuracion_evaluacion (version);

CREATE INDEX ix_configuracion_evaluacion_activa ON configuracion_evaluacion (activa);


CREATE TABLE auditoria (
	id SERIAL NOT NULL,
	usuario_id INTEGER,
	usuario_nombre VARCHAR(160) NOT NULL,
	accion VARCHAR(80) NOT NULL,
	recurso VARCHAR(160) NOT NULL,
	detalle JSON,
	fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(usuario_id) REFERENCES usuario (id)
);

CREATE INDEX ix_auditoria_usuario_id ON auditoria (usuario_id);

CREATE INDEX ix_auditoria_fecha_hora ON auditoria (fecha_hora);

CREATE INDEX ix_auditoria_accion ON auditoria (accion);


CREATE TABLE accion_plan (
	id SERIAL NOT NULL,
	plan_id INTEGER NOT NULL,
	descripcion VARCHAR(255) NOT NULL,
	completada BOOLEAN NOT NULL,
	fecha_limite DATE,
	fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(plan_id) REFERENCES plan_desarrollo (id)
);

CREATE INDEX ix_accion_plan_plan_id ON accion_plan (plan_id);


CREATE TABLE evaluacion (
	id SERIAL NOT NULL,
	colaborador_id INTEGER NOT NULL,
	configuracion_id INTEGER NOT NULL,
	periodo VARCHAR(20) NOT NULL,
	fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	version_modelo VARCHAR(40) NOT NULL,
	estado VARCHAR(15) NOT NULL,
	ejecutado_por_id INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(colaborador_id) REFERENCES colaborador (id),
	FOREIGN KEY(configuracion_id) REFERENCES configuracion_evaluacion (id),
	FOREIGN KEY(ejecutado_por_id) REFERENCES usuario (id)
);

CREATE INDEX ix_evaluacion_fecha ON evaluacion (fecha);

CREATE INDEX ix_evaluacion_periodo ON evaluacion (periodo);

CREATE INDEX ix_evaluacion_colaborador_id ON evaluacion (colaborador_id);

CREATE INDEX ix_evaluacion_configuracion_id ON evaluacion (configuracion_id);


CREATE TABLE resultado_evaluacion (
	id SERIAL NOT NULL,
	evaluacion_id INTEGER NOT NULL,
	puntuacion FLOAT,
	clasificacion VARCHAR(25),
	cobertura FLOAT NOT NULL,
	factores JSON,
	explicacion TEXT,
	explicacion_origen VARCHAR(40),
	fecha_explicacion TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (id),
	FOREIGN KEY(evaluacion_id) REFERENCES evaluacion (id)
);

CREATE UNIQUE INDEX ix_resultado_evaluacion_evaluacion_id ON resultado_evaluacion (evaluacion_id);


CREATE TABLE observacion (
	id SERIAL NOT NULL,
	evaluacion_id INTEGER,
	colaborador_id INTEGER,
	autor_id INTEGER NOT NULL,
	texto TEXT NOT NULL,
	fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(evaluacion_id) REFERENCES evaluacion (id),
	FOREIGN KEY(colaborador_id) REFERENCES colaborador (id),
	FOREIGN KEY(autor_id) REFERENCES usuario (id)
);

CREATE INDEX ix_observacion_colaborador_id ON observacion (colaborador_id);

CREATE INDEX ix_observacion_autor_id ON observacion (autor_id);

CREATE INDEX ix_observacion_evaluacion_id ON observacion (evaluacion_id);


CREATE TABLE revision_humana (
	id SERIAL NOT NULL,
	resultado_id INTEGER NOT NULL,
	usuario_id INTEGER NOT NULL,
	estado VARCHAR(15) NOT NULL,
	comentario TEXT NOT NULL,
	fecha TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(resultado_id) REFERENCES resultado_evaluacion (id),
	FOREIGN KEY(usuario_id) REFERENCES usuario (id)
);

CREATE INDEX ix_revision_humana_usuario_id ON revision_humana (usuario_id);

CREATE INDEX ix_revision_humana_resultado_id ON revision_humana (resultado_id);

-- =========================== 2) DATOS DE PRUEBA =======================

-- permiso (13 filas)
INSERT INTO permiso (id, codigo, descripcion) VALUES
(1, 'usuarios.gestionar', 'Gestionar usuarios, roles y permisos'),
(2, 'colaboradores.gestionar', 'Crear, actualizar y desactivar colaboradores'),
(3, 'colaboradores.consultar', 'Consultar colaboradores y perfiles'),
(4, 'indicadores.gestionar', 'Administrar indicadores y mediciones'),
(5, 'evaluaciones.ejecutar', 'Ejecutar el flujo de evaluación'),
(6, 'evaluaciones.revisar', 'Revisar resultados y registrar observaciones'),
(7, 'configuracion.gestionar', 'Configurar criterios, pesos y umbrales'),
(8, 'reportes.consultar', 'Ver paneles y reportes'),
(9, 'reportes.exportar', 'Exportar reportes'),
(10, 'auditoria.consultar', 'Consultar el registro de auditoría'),
(11, 'ia.usar', 'Usar consultas y explicaciones asistidas por IA'),
(12, 'planes.consultar', 'Consultar planes de desarrollo y sucesión'),
(13, 'planes.gestionar', 'Administrar planes de desarrollo y sucesión');

-- rol (4 filas)
INSERT INTO rol (id, nombre, descripcion) VALUES
(1, 'ADMINISTRADOR', 'Rol Administrador'),
(2, 'GESTOR_TALENTO', 'Rol Gestor_Talento'),
(3, 'EVALUADOR', 'Rol Evaluador'),
(4, 'CONSULTA', 'Rol Consulta');

-- rol_permiso (32 filas)
INSERT INTO rol_permiso (rol_id, permiso_id) VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(1, 5),
(1, 6),
(1, 7),
(1, 8),
(1, 9),
(1, 10),
(1, 11),
(1, 12),
(1, 13),
(4, 3),
(4, 8),
(3, 3),
(3, 5),
(3, 6),
(3, 8),
(3, 11),
(3, 12),
(2, 2),
(2, 3),
(2, 4),
(2, 5),
(2, 6),
(2, 7),
(2, 8),
(2, 9),
(2, 11),
(2, 12),
(2, 13);

-- usuario (4 filas)
INSERT INTO usuario (id, nombre, correo, password_hash, rol_id, estado, creado_en) VALUES
(1, 'Administrador del Sistema', 'admin@develop.com.mx', 'pbkdf2_sha256$390000$6a0b17f94dd5f88ecae1c96132108175$4589876183ea1882b5d0c1d14cf4ff6941a2229cc62bffc3eaa0d9ffa60fcf84', 1, TRUE, '2026-10-17 19:24:21'),
(2, 'Gestora de Talento', 'gestor@develop.com.mx', 'pbkdf2_sha256$390000$2bf0c0b7ff90d299946e178f0ac530d2$9b7c8520a50fc26b1a6168b10c2a0d179a4cbf8383c14a1198758e91a774b81f', 2, TRUE, '2026-10-17 19:24:22'),
(3, 'Evaluador Líder', 'evaluador@develop.com.mx', 'pbkdf2_sha256$390000$228d2422c864ae40b35b088cc2cca78f$a7e5d7d1661c31cdcf14386ee39645214f064ef7fbd478efbf7c4a235c48ffba', 3, TRUE, '2026-10-17 19:24:22'),
(4, 'Usuario Consulta', 'consulta@develop.com.mx', 'pbkdf2_sha256$390000$25f6bc75ba4d85d6d368d564aa1da24b$e56fc7f813fe0f0d7c0b7dcd61dae51f831f105cdb86185b498cd7883663d7ad', 4, TRUE, '2026-10-17 19:24:22');

-- colaborador (12 filas)
INSERT INTO colaborador (id, codigo, nombre, area, puesto, fecha_ingreso, estado) VALUES
(1, 'COL-001', 'Ana Sofía Mendoza Reyes', 'Tecnología', 'Desarrolladora Senior', '2019-03-11', TRUE),
(2, 'COL-002', 'Carlos Emilio Ramírez Soto', 'Tecnología', 'Ingeniero de Datos', '2021-07-05', TRUE),
(3, 'COL-003', 'Lucía Fernanda Ortiz Cruz', 'Tecnología', 'Desarrolladora Frontend', '2022-01-17', TRUE),
(4, 'COL-004', 'Diego Alejandro Torres Lima', 'Recursos Humanos', 'Especialista de Talento', '2020-09-21', TRUE),
(5, 'COL-005', 'María José Vargas Nieto', 'Recursos Humanos', 'Socio de negocio', '2018-02-12', TRUE),
(6, 'COL-006', 'Jorge Luis Salgado Prieto', 'Finanzas', 'Analista Financiero', '2023-04-03', TRUE),
(7, 'COL-007', 'Valeria Campos Domínguez', 'Finanzas', 'Contralora', '2017-11-27', TRUE),
(8, 'COL-008', 'Rodrigo Esteban Navarro León', 'Comercial', 'Ejecutivo de Cuentas', '2022-08-15', TRUE),
(9, 'COL-009', 'Daniela Paola Ríos Castañeda', 'Comercial', 'Gerente Comercial', '2019-06-10', TRUE),
(10, 'COL-010', 'Fernando Miguel Ávila Santos', 'Operaciones', 'Coordinador de Operaciones', '2021-01-25', TRUE),
(11, 'COL-011', 'Regina Ocampo Ruiz', 'Operaciones', 'Analista de Procesos', '2023-10-02', TRUE),
(12, 'COL-012', 'Pablo Adrián Quiroz Mena', 'Operaciones', 'Técnico de Soporte', '2024-05-20', TRUE);

-- indicador (11 filas)
INSERT INTO indicador (id, codigo, nombre, tipo, direccion, activo) VALUES
(1, 'DESEMPENO_GLOBAL', 'Desempeño global', 'DESEMPENO', 'MAYOR_MEJOR', TRUE),
(2, 'CRECIMIENTO_DESEMPENO', 'Crecimiento de desempeño vs. periodo anterior', 'DESEMPENO', 'MAYOR_MEJOR', TRUE),
(3, 'LIDERAZGO', 'Competencia de liderazgo', 'COMPETENCIA', 'MAYOR_MEJOR', TRUE),
(4, 'COMUNICACION', 'Competencia de comunicación', 'COMPETENCIA', 'MAYOR_MEJOR', TRUE),
(5, 'COLABORACION', 'Competencia de colaboración', 'COMPETENCIA', 'MAYOR_MEJOR', TRUE),
(6, 'PUNTAJE_CAPACITACION', 'Puntaje promedio de capacitación', 'CAPACITACION', 'MAYOR_MEJOR', TRUE),
(7, 'CURSOS_APROBADOS', 'Cursos aprobados (normalizado 0-100)', 'CAPACITACION', 'MAYOR_MEJOR', TRUE),
(8, 'ANIOS_EXPERIENCIA', 'Años de experiencia (normalizado)', 'EXPERIENCIA', 'MAYOR_MEJOR', TRUE),
(9, 'CUMPLIMIENTO_OBJETIVOS', 'Cumplimiento de objetivos', 'OBJETIVO', 'MAYOR_MEJOR', TRUE),
(10, 'IMPACTO_PROYECTOS', 'Impacto en proyectos organizacionales', 'ORGANIZACIONAL', 'MAYOR_MEJOR', TRUE),
(11, 'ROTACION_EQUIPO', 'Rotación del equipo a cargo', 'ORGANIZACIONAL', 'MENOR_MEJOR', TRUE);

-- area_evaluacion (5 filas)
INSERT INTO area_evaluacion (id, area) VALUES
(1, 'Comercial'),
(2, 'Finanzas'),
(3, 'Operaciones'),
(4, 'Recursos Humanos'),
(5, 'Tecnología');

-- area_indicador (55 filas)
INSERT INTO area_indicador (area_evaluacion_id, indicador_id) VALUES
(4, 1),
(4, 2),
(4, 3),
(4, 4),
(4, 5),
(4, 6),
(4, 7),
(4, 8),
(4, 9),
(4, 10),
(4, 11),
(2, 1),
(2, 2),
(2, 3),
(2, 4),
(2, 5),
(2, 6),
(2, 7),
(2, 8),
(2, 9),
(2, 10),
(2, 11),
(5, 1),
(5, 2),
(5, 3),
(5, 4),
(5, 5),
(5, 6),
(5, 7),
(5, 8),
(5, 9),
(5, 10),
(5, 11),
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(1, 5),
(1, 6),
(1, 7),
(1, 8),
(1, 9),
(1, 10),
(1, 11),
(3, 1),
(3, 2),
(3, 3),
(3, 4),
(3, 5),
(3, 6),
(3, 7),
(3, 8),
(3, 9),
(3, 10),
(3, 11);

-- configuracion_evaluacion (1 filas)
INSERT INTO configuracion_evaluacion (id, version, nombre, criterios, reglas, umbral_hipo, activa, creado_por_id, fecha_creacion) VALUES
(1, 1, 'Criterios HiPo v1 — cuadro de mando de talento', '{"pesos": {"DESEMPENO_GLOBAL": 0.2, "CRECIMIENTO_DESEMPENO": 0.1, "LIDERAZGO": 0.12, "COMUNICACION": 0.08, "COLABORACION": 0.06, "PUNTAJE_CAPACITACION": 0.1, "CURSOS_APROBADOS": 0.05, "ANIOS_EXPERIENCIA": 0.07, "CUMPLIMIENTO_OBJETIVOS": 0.12, "IMPACTO_PROYECTOS": 0.06, "ROTACION_EQUIPO": 0.04}}'::json, '{"cobertura_minima": 0.8, "umbral_desarrollo_rel": 0.85}'::json, 75.0, TRUE, 1, '2026-10-17 19:24:22');

-- medicion_indicador (257 filas)
INSERT INTO medicion_indicador (id, colaborador_id, indicador_id, periodo, valor, validez, comentario, fecha_registro) VALUES
(1, 1, 1, '2025-S2', 94.03, 'VALIDA', '', '2026-10-17 19:24:22'),
(2, 1, 2, '2025-S2', 98.32, 'VALIDA', '', '2026-10-17 19:24:22'),
(3, 1, 3, '2025-S2', 90.68, 'VALIDA', '', '2026-10-17 19:24:22'),
(4, 1, 4, '2025-S2', 94.68, 'VALIDA', '', '2026-10-17 19:24:22'),
(5, 1, 5, '2025-S2', 94.57, 'VALIDA', '', '2026-10-17 19:24:22'),
(6, 1, 6, '2025-S2', 97.22, 'VALIDA', '', '2026-10-17 19:24:22'),
(7, 1, 7, '2025-S2', 95.04, 'VALIDA', '', '2026-10-17 19:24:22'),
(8, 1, 8, '2025-S2', 23.97, 'VALIDA', '', '2026-10-17 19:24:22'),
(9, 1, 9, '2025-S2', 97.8, 'VALIDA', '', '2026-10-17 19:24:22'),
(10, 1, 10, '2025-S2', 97.78, 'VALIDA', '', '2026-10-17 19:24:22'),
(11, 1, 11, '2025-S2', 29.35, 'VALIDA', '', '2026-10-17 19:24:22'),
(12, 1, 1, '2026-S1', 91.02, 'VALIDA', '', '2026-10-17 19:24:22'),
(13, 1, 2, '2026-S1', 99.15, 'INVALIDA', '', '2026-10-17 19:24:22'),
(14, 1, 3, '2026-S1', 100.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(15, 1, 4, '2026-S1', 88.92, 'VALIDA', '', '2026-10-17 19:24:22'),
(16, 1, 5, '2026-S1', 94.69, 'VALIDA', '', '2026-10-17 19:24:22'),
(17, 1, 6, '2026-S1', 93.49, 'VALIDA', '', '2026-10-17 19:24:22'),
(18, 1, 7, '2026-S1', 96.45, 'VALIDA', '', '2026-10-17 19:24:22'),
(19, 1, 8, '2026-S1', 16.9, 'VALIDA', '', '2026-10-17 19:24:22'),
(20, 1, 9, '2026-S1', 92.36, 'VALIDA', '', '2026-10-17 19:24:22'),
(21, 1, 10, '2026-S1', 92.79, 'VALIDA', '', '2026-10-17 19:24:22'),
(22, 1, 11, '2026-S1', 27.18, 'VALIDA', '', '2026-10-17 19:24:22'),
(23, 2, 1, '2025-S2', 83.28, 'VALIDA', '', '2026-10-17 19:24:22'),
(24, 2, 2, '2025-S2', 84.4, 'VALIDA', '', '2026-10-17 19:24:22'),
(25, 2, 3, '2025-S2', 88.2, 'VALIDA', '', '2026-10-17 19:24:22'),
(26, 2, 4, '2025-S2', 82.24, 'VALIDA', '', '2026-10-17 19:24:22'),
(27, 2, 5, '2025-S2', 82.95, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(28, 2, 6, '2025-S2', 77.5, 'VALIDA', '', '2026-10-17 19:24:22'),
(29, 2, 7, '2025-S2', 78.75, 'VALIDA', '', '2026-10-17 19:24:22'),
(30, 2, 8, '2025-S2', 20.74, 'VALIDA', '', '2026-10-17 19:24:22'),
(31, 2, 9, '2025-S2', 78.43, 'VALIDA', '', '2026-10-17 19:24:22'),
(32, 2, 10, '2025-S2', 82.84, 'VALIDA', '', '2026-10-17 19:24:22'),
(33, 2, 11, '2025-S2', 18.91, 'VALIDA', '', '2026-10-17 19:24:22'),
(34, 2, 1, '2026-S1', 84.72, 'VALIDA', '', '2026-10-17 19:24:22'),
(35, 2, 2, '2026-S1', 82.83, 'VALIDA', '', '2026-10-17 19:24:22'),
(36, 2, 3, '2026-S1', 89.05, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(37, 2, 4, '2026-S1', 83.92, 'VALIDA', '', '2026-10-17 19:24:22'),
(38, 2, 5, '2026-S1', 80.89, 'VALIDA', '', '2026-10-17 19:24:22'),
(39, 2, 6, '2026-S1', 83.22, 'VALIDA', '', '2026-10-17 19:24:22'),
(40, 2, 7, '2026-S1', 87.81, 'VALIDA', '', '2026-10-17 19:24:22'),
(41, 2, 8, '2026-S1', 15.81, 'VALIDA', '', '2026-10-17 19:24:22'),
(42, 2, 9, '2026-S1', 77.6, 'VALIDA', '', '2026-10-17 19:24:22'),
(43, 2, 10, '2026-S1', 84.37, 'VALIDA', '', '2026-10-17 19:24:22'),
(44, 2, 11, '2026-S1', 22.43, 'VALIDA', '', '2026-10-17 19:24:22'),
(45, 3, 1, '2025-S2', 78.06, 'VALIDA', '', '2026-10-17 19:24:22'),
(46, 3, 2, '2025-S2', 72.83, 'VALIDA', '', '2026-10-17 19:24:22'),
(47, 3, 3, '2025-S2', 76.91, 'VALIDA', '', '2026-10-17 19:24:22'),
(48, 3, 4, '2025-S2', 73.69, 'VALIDA', '', '2026-10-17 19:24:22'),
(49, 3, 5, '2025-S2', 76.98, 'VALIDA', '', '2026-10-17 19:24:22'),
(50, 3, 6, '2025-S2', 78.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(51, 3, 7, '2025-S2', 75.27, 'VALIDA', '', '2026-10-17 19:24:22'),
(52, 3, 8, '2025-S2', 14.38, 'VALIDA', '', '2026-10-17 19:24:22'),
(53, 3, 9, '2025-S2', 78.58, 'VALIDA', '', '2026-10-17 19:24:22'),
(54, 3, 10, '2025-S2', 77.11, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(55, 3, 11, '2025-S2', 12.17, 'VALIDA', '', '2026-10-17 19:24:22'),
(56, 3, 1, '2026-S1', 72.98, 'VALIDA', '', '2026-10-17 19:24:22'),
(57, 3, 2, '2026-S1', 75.97, 'VALIDA', '', '2026-10-17 19:24:22'),
(58, 3, 3, '2026-S1', 72.39, 'VALIDA', '', '2026-10-17 19:24:22'),
(59, 3, 4, '2026-S1', 67.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(60, 3, 5, '2026-S1', 78.19, 'VALIDA', '', '2026-10-17 19:24:22'),
(61, 3, 6, '2026-S1', 76.53, 'VALIDA', '', '2026-10-17 19:24:22'),
(62, 3, 7, '2026-S1', 74.45, 'VALIDA', '', '2026-10-17 19:24:22'),
(63, 3, 8, '2026-S1', 19.68, 'VALIDA', '', '2026-10-17 19:24:22'),
(64, 3, 9, '2026-S1', 74.62, 'VALIDA', '', '2026-10-17 19:24:22'),
(65, 3, 10, '2026-S1', 70.76, 'VALIDA', '', '2026-10-17 19:24:22'),
(66, 3, 11, '2026-S1', 20.63, 'VALIDA', '', '2026-10-17 19:24:22'),
(67, 4, 1, '2025-S2', 81.9, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(68, 4, 2, '2025-S2', 77.62, 'VALIDA', '', '2026-10-17 19:24:22'),
(69, 4, 3, '2025-S2', 83.06, 'VALIDA', '', '2026-10-17 19:24:22'),
(70, 4, 4, '2025-S2', 86.51, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(71, 4, 5, '2025-S2', 77.01, 'VALIDA', '', '2026-10-17 19:24:22'),
(72, 4, 6, '2025-S2', 87.22, 'VALIDA', '', '2026-10-17 19:24:22'),
(73, 4, 7, '2025-S2', 86.98, 'VALIDA', '', '2026-10-17 19:24:22'),
(74, 4, 8, '2025-S2', 16.74, 'VALIDA', '', '2026-10-17 19:24:22'),
(75, 4, 9, '2025-S2', 82.24, 'VALIDA', '', '2026-10-17 19:24:22'),
(76, 4, 10, '2025-S2', 76.17, 'VALIDA', '', '2026-10-17 19:24:22'),
(77, 4, 11, '2025-S2', 26.25, 'VALIDA', '', '2026-10-17 19:24:22'),
(78, 4, 1, '2026-S1', 80.16, 'VALIDA', '', '2026-10-17 19:24:22'),
(79, 4, 2, '2026-S1', 85.23, 'VALIDA', '', '2026-10-17 19:24:22'),
(80, 4, 3, '2026-S1', 82.12, 'VALIDA', '', '2026-10-17 19:24:22'),
(81, 4, 4, '2026-S1', 79.64, 'VALIDA', '', '2026-10-17 19:24:22'),
(82, 4, 5, '2026-S1', 77.46, 'VALIDA', '', '2026-10-17 19:24:22'),
(83, 4, 6, '2026-S1', 82.86, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(84, 4, 7, '2026-S1', 77.85, 'VALIDA', '', '2026-10-17 19:24:22'),
(85, 4, 8, '2026-S1', 17.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(86, 4, 9, '2026-S1', 83.18, 'VALIDA', '', '2026-10-17 19:24:22'),
(87, 4, 10, '2026-S1', 76.83, 'VALIDA', '', '2026-10-17 19:24:22'),
(88, 4, 11, '2026-S1', 17.95, 'VALIDA', '', '2026-10-17 19:24:22'),
(89, 5, 1, '2025-S2', 87.34, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(90, 5, 2, '2025-S2', 96.87, 'VALIDA', '', '2026-10-17 19:24:22'),
(91, 5, 3, '2025-S2', 95.86, 'VALIDA', '', '2026-10-17 19:24:22'),
(92, 5, 4, '2025-S2', 95.33, 'VALIDA', '', '2026-10-17 19:24:22'),
(93, 5, 5, '2025-S2', 88.35, 'VALIDA', '', '2026-10-17 19:24:22'),
(94, 5, 6, '2025-S2', 96.22, 'VALIDA', '', '2026-10-17 19:24:22'),
(95, 5, 7, '2025-S2', 98.28, 'VALIDA', '', '2026-10-17 19:24:22'),
(96, 5, 8, '2025-S2', 25.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(97, 5, 9, '2025-S2', 91.9, 'VALIDA', '', '2026-10-17 19:24:22'),
(98, 5, 10, '2025-S2', 87.74, 'VALIDA', '', '2026-10-17 19:24:22'),
(99, 5, 11, '2025-S2', 24.77, 'VALIDA', '', '2026-10-17 19:24:22'),
(100, 5, 1, '2026-S1', 92.77, 'VALIDA', '', '2026-10-17 19:24:22'),
(101, 5, 2, '2026-S1', 91.79, 'VALIDA', '', '2026-10-17 19:24:22'),
(102, 5, 3, '2026-S1', 90.71, 'VALIDA', '', '2026-10-17 19:24:22'),
(103, 5, 4, '2026-S1', 88.24, 'VALIDA', '', '2026-10-17 19:24:22'),
(104, 5, 5, '2026-S1', 96.36, 'VALIDA', '', '2026-10-17 19:24:22'),
(105, 5, 6, '2026-S1', 96.97, 'VALIDA', '', '2026-10-17 19:24:22'),
(106, 5, 7, '2026-S1', 98.24, 'VALIDA', '', '2026-10-17 19:24:22'),
(107, 5, 8, '2026-S1', 23.87, 'VALIDA', '', '2026-10-17 19:24:22'),
(108, 5, 9, '2026-S1', 96.2, 'VALIDA', '', '2026-10-17 19:24:22'),
(109, 5, 10, '2026-S1', 94.84, 'VALIDA', '', '2026-10-17 19:24:22'),
(110, 5, 11, '2026-S1', 24.86, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(111, 6, 1, '2025-S2', 70.74, 'VALIDA', '', '2026-10-17 19:24:22'),
(112, 6, 2, '2025-S2', 70.46, 'VALIDA', '', '2026-10-17 19:24:22'),
(113, 6, 3, '2025-S2', 72.59, 'VALIDA', '', '2026-10-17 19:24:22'),
(114, 6, 4, '2025-S2', 70.82, 'VALIDA', '', '2026-10-17 19:24:22'),
(115, 6, 5, '2025-S2', 67.54, 'VALIDA', '', '2026-10-17 19:24:22'),
(116, 6, 6, '2025-S2', 70.67, 'VALIDA', '', '2026-10-17 19:24:22'),
(117, 6, 7, '2025-S2', 67.16, 'VALIDA', '', '2026-10-17 19:24:22'),
(118, 6, 8, '2025-S2', 9.06, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(119, 6, 9, '2025-S2', 73.11, 'VALIDA', '', '2026-10-17 19:24:22'),
(120, 6, 10, '2025-S2', 66.23, 'VALIDA', '', '2026-10-17 19:24:22'),
(121, 6, 11, '2025-S2', 16.08, 'VALIDA', '', '2026-10-17 19:24:22'),
(122, 6, 1, '2026-S1', 74.05, 'VALIDA', '', '2026-10-17 19:24:22'),
(123, 6, 2, '2026-S1', 67.78, 'VALIDA', '', '2026-10-17 19:24:22'),
(124, 6, 3, '2026-S1', 64.75, 'VALIDA', '', '2026-10-17 19:24:22'),
(125, 6, 4, '2026-S1', 74.78, 'VALIDA', '', '2026-10-17 19:24:22'),
(126, 6, 5, '2026-S1', 68.97, 'VALIDA', '', '2026-10-17 19:24:22'),
(127, 6, 6, '2026-S1', 65.16, 'VALIDA', '', '2026-10-17 19:24:22'),
(128, 6, 7, '2026-S1', 65.48, 'VALIDA', '', '2026-10-17 19:24:22'),
(129, 6, 8, '2026-S1', 13.92, 'VALIDA', '', '2026-10-17 19:24:22'),
(130, 6, 9, '2026-S1', 68.2, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(131, 6, 10, '2026-S1', 71.29, 'VALIDA', '', '2026-10-17 19:24:22'),
(132, 6, 11, '2026-S1', 17.38, 'VALIDA', '', '2026-10-17 19:24:22'),
(133, 7, 1, '2025-S2', 92.99, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(134, 7, 2, '2025-S2', 94.75, 'VALIDA', '', '2026-10-17 19:24:22'),
(135, 7, 3, '2025-S2', 99.74, 'INVALIDA', '', '2026-10-17 19:24:22'),
(136, 7, 4, '2025-S2', 99.54, 'VALIDA', '', '2026-10-17 19:24:22'),
(137, 7, 5, '2025-S2', 100.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(138, 7, 6, '2025-S2', 100.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(139, 7, 7, '2025-S2', 98.02, 'VALIDA', '', '2026-10-17 19:24:22'),
(140, 7, 8, '2025-S2', 17.36, 'VALIDA', '', '2026-10-17 19:24:22'),
(141, 7, 9, '2025-S2', 92.67, 'VALIDA', '', '2026-10-17 19:24:22'),
(142, 7, 10, '2025-S2', 98.8, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(143, 7, 11, '2025-S2', 30.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(144, 7, 1, '2026-S1', 100.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(145, 7, 2, '2026-S1', 93.31, 'VALIDA', '', '2026-10-17 19:24:22'),
(146, 7, 3, '2026-S1', 97.86, 'VALIDA', '', '2026-10-17 19:24:22'),
(147, 7, 4, '2026-S1', 96.63, 'VALIDA', '', '2026-10-17 19:24:22'),
(148, 7, 5, '2026-S1', 90.71, 'VALIDA', '', '2026-10-17 19:24:22'),
(149, 7, 6, '2026-S1', 96.97, 'VALIDA', '', '2026-10-17 19:24:22'),
(150, 7, 7, '2026-S1', 89.55, 'VALIDA', '', '2026-10-17 19:24:22'),
(151, 7, 8, '2026-S1', 21.35, 'VALIDA', '', '2026-10-17 19:24:22'),
(152, 7, 9, '2026-S1', 92.07, 'VALIDA', '', '2026-10-17 19:24:22'),
(153, 7, 10, '2026-S1', 91.83, 'VALIDA', '', '2026-10-17 19:24:22'),
(154, 7, 11, '2026-S1', 28.28, 'VALIDA', '', '2026-10-17 19:24:22'),
(155, 8, 1, '2025-S2', 81.22, 'VALIDA', '', '2026-10-17 19:24:22'),
(156, 8, 2, '2025-S2', 74.76, 'VALIDA', '', '2026-10-17 19:24:22'),
(157, 8, 3, '2025-S2', 71.77, 'VALIDA', '', '2026-10-17 19:24:22'),
(158, 8, 4, '2025-S2', 73.32, 'VALIDA', '', '2026-10-17 19:24:22'),
(159, 8, 5, '2025-S2', 73.17, 'VALIDA', '', '2026-10-17 19:24:22'),
(160, 8, 6, '2025-S2', 81.33, 'VALIDA', '', '2026-10-17 19:24:22'),
(161, 8, 7, '2025-S2', 80.07, 'VALIDA', '', '2026-10-17 19:24:22'),
(162, 8, 8, '2025-S2', 17.2, 'VALIDA', '', '2026-10-17 19:24:22'),
(163, 8, 9, '2025-S2', 76.17, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(164, 8, 10, '2025-S2', 77.6, 'VALIDA', '', '2026-10-17 19:24:22'),
(165, 8, 11, '2025-S2', 16.61, 'VALIDA', '', '2026-10-17 19:24:22'),
(166, 8, 1, '2026-S1', 70.14, 'VALIDA', '', '2026-10-17 19:24:22'),
(167, 8, 2, '2026-S1', 75.65, 'INVALIDA', '', '2026-10-17 19:24:22'),
(168, 8, 3, '2026-S1', 78.15, 'INVALIDA', '', '2026-10-17 19:24:22'),
(169, 8, 4, '2026-S1', 81.13, 'VALIDA', '', '2026-10-17 19:24:22'),
(170, 8, 5, '2026-S1', 74.79, 'VALIDA', '', '2026-10-17 19:24:22'),
(171, 8, 6, '2026-S1', 81.41, 'INVALIDA', '', '2026-10-17 19:24:22'),
(172, 8, 7, '2026-S1', 79.95, 'VALIDA', '', '2026-10-17 19:24:22'),
(173, 8, 8, '2026-S1', 11.81, 'VALIDA', '', '2026-10-17 19:24:22'),
(174, 8, 9, '2026-S1', 77.64, 'VALIDA', '', '2026-10-17 19:24:22'),
(175, 8, 10, '2026-S1', 75.69, 'VALIDA', '', '2026-10-17 19:24:22'),
(176, 8, 11, '2026-S1', 19.77, 'VALIDA', '', '2026-10-17 19:24:22'),
(177, 9, 1, '2025-S2', 92.54, 'VALIDA', '', '2026-10-17 19:24:22'),
(178, 9, 2, '2025-S2', 95.73, 'VALIDA', '', '2026-10-17 19:24:22'),
(179, 9, 3, '2025-S2', 94.77, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(180, 9, 4, '2025-S2', 93.43, 'VALIDA', '', '2026-10-17 19:24:22'),
(181, 9, 5, '2025-S2', 92.67, 'VALIDA', '', '2026-10-17 19:24:22'),
(182, 9, 6, '2025-S2', 89.47, 'VALIDA', '', '2026-10-17 19:24:22'),
(183, 9, 7, '2025-S2', 86.66, 'VALIDA', '', '2026-10-17 19:24:22'),
(184, 9, 8, '2025-S2', 25.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(185, 9, 9, '2025-S2', 87.61, 'VALIDA', '', '2026-10-17 19:24:22'),
(186, 9, 10, '2025-S2', 91.99, 'VALIDA', '', '2026-10-17 19:24:22'),
(187, 9, 11, '2025-S2', 30.0, 'VALIDA', '', '2026-10-17 19:24:22'),
(188, 9, 1, '2026-S1', 96.56, 'VALIDA', '', '2026-10-17 19:24:22'),
(189, 9, 2, '2026-S1', 92.73, 'VALIDA', '', '2026-10-17 19:24:22'),
(190, 9, 3, '2026-S1', 91.11, 'VALIDA', '', '2026-10-17 19:24:22'),
(191, 9, 4, '2026-S1', 93.79, 'VALIDA', '', '2026-10-17 19:24:22'),
(192, 9, 5, '2026-S1', 88.14, 'VALIDA', '', '2026-10-17 19:24:22'),
(193, 9, 6, '2026-S1', 92.11, 'VALIDA', '', '2026-10-17 19:24:22'),
(194, 9, 7, '2026-S1', 86.95, 'VALIDA', '', '2026-10-17 19:24:22'),
(195, 9, 8, '2026-S1', 21.89, 'VALIDA', '', '2026-10-17 19:24:22'),
(196, 9, 9, '2026-S1', 96.67, 'VALIDA', '', '2026-10-17 19:24:22'),
(197, 9, 10, '2026-S1', 93.96, 'VALIDA', '', '2026-10-17 19:24:22'),
(198, 9, 11, '2026-S1', 27.07, 'VALIDA', '', '2026-10-17 19:24:22'),
(199, 10, 1, '2025-S2', 73.87, 'VALIDA', '', '2026-10-17 19:24:22'),
(200, 10, 2, '2025-S2', 79.63, 'VALIDA', '', '2026-10-17 19:24:22'),
(201, 10, 3, '2025-S2', 80.76, 'INVALIDA', '', '2026-10-17 19:24:22'),
(202, 10, 4, '2025-S2', 74.99, 'VALIDA', '', '2026-10-17 19:24:22'),
(203, 10, 5, '2025-S2', 75.27, 'VALIDA', '', '2026-10-17 19:24:22'),
(204, 10, 6, '2025-S2', 79.45, 'VALIDA', '', '2026-10-17 19:24:22'),
(205, 10, 7, '2025-S2', 79.39, 'VALIDA', '', '2026-10-17 19:24:22'),
(206, 10, 8, '2025-S2', 8.94, 'VALIDA', '', '2026-10-17 19:24:22'),
(207, 10, 9, '2025-S2', 73.22, 'VALIDA', '', '2026-10-17 19:24:22'),
(208, 10, 10, '2025-S2', 70.65, 'VALIDA', '', '2026-10-17 19:24:22'),
(209, 10, 11, '2025-S2', 13.76, 'VALIDA', '', '2026-10-17 19:24:22'),
(210, 10, 1, '2026-S1', 74.61, 'INVALIDA', '', '2026-10-17 19:24:22'),
(211, 10, 2, '2026-S1', 77.52, 'VALIDA', '', '2026-10-17 19:24:22'),
(212, 10, 3, '2026-S1', 76.2, 'VALIDA', '', '2026-10-17 19:24:22'),
(213, 10, 4, '2026-S1', 72.97, 'VALIDA', '', '2026-10-17 19:24:22'),
(214, 10, 5, '2026-S1', 70.25, 'VALIDA', '', '2026-10-17 19:24:22'),
(215, 10, 6, '2026-S1', 78.74, 'VALIDA', '', '2026-10-17 19:24:22'),
(216, 10, 7, '2026-S1', 74.27, 'VALIDA', '', '2026-10-17 19:24:22'),
(217, 10, 8, '2026-S1', 9.91, 'VALIDA', '', '2026-10-17 19:24:22'),
(218, 10, 9, '2026-S1', 69.85, 'VALIDA', '', '2026-10-17 19:24:22'),
(219, 10, 10, '2026-S1', 72.54, 'VALIDA', '', '2026-10-17 19:24:22'),
(220, 10, 11, '2026-S1', 14.95, 'VALIDA', '', '2026-10-17 19:24:22'),
(221, 11, 1, '2025-S2', 80.88, 'VALIDA', '', '2026-10-17 19:24:22'),
(222, 11, 2, '2025-S2', 85.69, 'VALIDA', '', '2026-10-17 19:24:22'),
(223, 11, 3, '2025-S2', 85.09, 'VALIDA', '', '2026-10-17 19:24:22'),
(224, 11, 4, '2025-S2', 76.92, 'VALIDA', '', '2026-10-17 19:24:22'),
(225, 11, 5, '2025-S2', 77.44, 'VALIDA', '', '2026-10-17 19:24:22'),
(226, 11, 6, '2025-S2', 78.98, 'VALIDA', '', '2026-10-17 19:24:22'),
(227, 11, 7, '2025-S2', 79.72, 'VALIDA', '', '2026-10-17 19:24:22'),
(228, 11, 8, '2025-S2', 15.9, 'VALIDA', '', '2026-10-17 19:24:22'),
(229, 11, 9, '2025-S2', 83.72, 'VALIDA', '', '2026-10-17 19:24:22'),
(230, 11, 10, '2025-S2', 76.33, 'VALIDA', '', '2026-10-17 19:24:22'),
(231, 11, 11, '2025-S2', 25.07, 'VALIDA', '', '2026-10-17 19:24:22'),
(232, 11, 1, '2026-S1', 84.89, 'VALIDA', '', '2026-10-17 19:24:22'),
(233, 11, 2, '2026-S1', 76.54, 'VALIDA', '', '2026-10-17 19:24:22'),
(234, 11, 3, '2026-S1', 77.61, 'VALIDA', '', '2026-10-17 19:24:22'),
(235, 11, 4, '2026-S1', 81.54, 'INVALIDA', '', '2026-10-17 19:24:22'),
(236, 11, 5, '2026-S1', 78.32, 'VALIDA', '', '2026-10-17 19:24:22'),
(237, 11, 6, '2026-S1', 79.61, 'VALIDA', '', '2026-10-17 19:24:22'),
(238, 11, 7, '2026-S1', 83.4, 'VALIDA', '', '2026-10-17 19:24:22'),
(239, 11, 8, '2026-S1', 15.36, 'VALIDA', '', '2026-10-17 19:24:22'),
(240, 11, 9, '2026-S1', 85.87, 'VALIDA', '', '2026-10-17 19:24:22'),
(241, 11, 10, '2026-S1', 84.97, 'VALIDA', '', '2026-10-17 19:24:22'),
(242, 11, 11, '2026-S1', 23.05, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(243, 12, 1, '2025-S2', 61.72, 'VALIDA', '', '2026-10-17 19:24:22'),
(244, 12, 2, '2025-S2', 63.17, 'VALIDA', '', '2026-10-17 19:24:22'),
(245, 12, 3, '2025-S2', 67.89, 'PENDIENTE', '', '2026-10-17 19:24:22'),
(246, 12, 4, '2025-S2', 65.91, 'VALIDA', '', '2026-10-17 19:24:22'),
(247, 12, 5, '2025-S2', 63.21, 'VALIDA', '', '2026-10-17 19:24:22'),
(248, 12, 6, '2025-S2', 64.18, 'VALIDA', '', '2026-10-17 19:24:22'),
(249, 12, 7, '2025-S2', 64.91, 'VALIDA', '', '2026-10-17 19:24:22'),
(250, 12, 8, '2025-S2', 9.14, 'VALIDA', '', '2026-10-17 19:24:22'),
(251, 12, 9, '2025-S2', 61.84, 'VALIDA', '', '2026-10-17 19:24:22'),
(252, 12, 10, '2025-S2', 69.42, 'VALIDA', '', '2026-10-17 19:24:22'),
(253, 12, 11, '2025-S2', 7.97, 'VALIDA', '', '2026-10-17 19:24:22'),
(254, 12, 1, '2026-S1', 64.69, 'VALIDA', '', '2026-10-17 19:24:22'),
(255, 12, 2, '2026-S1', 66.76, 'VALIDA', '', '2026-10-17 19:24:22'),
(256, 12, 3, '2026-S1', 67.51, 'VALIDA', '', '2026-10-17 19:24:22'),
(257, 12, 4, '2026-S1', 59.34, 'VALIDA', '', '2026-10-17 19:24:22');

-- plan_desarrollo (5 filas)
INSERT INTO plan_desarrollo (id, colaborador_id, titulo, objetivo, foco, fecha_inicio, fecha_fin, estado, progreso, responsable_id, creado_por_id, fecha_creacion, fecha_actualizacion) VALUES
(1, 1, 'Ruta de sucesión a Tech Lead', 'Preparar a Ana Sofía Mendoza Reyes para mayores responsabilidades mediante acciones de desarrollo trazables.', 'liderazgo', '2026-01-15', '2026-12-15', 'EN_PROGRESO', 66.7, NULL, 1, '2026-10-17 19:24:22', NULL),
(2, 5, 'Preparación para Dirección de Personas', 'Preparar a María José Vargas Nieto para mayores responsabilidades mediante acciones de desarrollo trazables.', 'liderazgo', '2026-03-01', '2026-11-30', 'EN_PROGRESO', 66.7, NULL, 1, '2026-10-17 19:24:22', NULL),
(3, 7, 'Desarrollo como Contralora Corporativa', 'Preparar a Valeria Campos Domínguez para mayores responsabilidades mediante acciones de desarrollo trazables.', 'especialista', '2025-10-01', '2026-08-31', 'EN_PROGRESO', 50.0, NULL, 1, '2026-10-17 19:24:22', NULL),
(4, 9, 'Plan de sucesión comercial', 'Preparar a Daniela Paola Ríos Castañeda para mayores responsabilidades mediante acciones de desarrollo trazables.', 'liderazgo', '2026-05-01', '2026-12-31', 'PLANIFICADO', 0.0, NULL, 1, '2026-10-17 19:24:22', NULL),
(5, 12, 'Fortalecimiento de competencias base', 'Preparar a Pablo Adrián Quiroz Mena para mayores responsabilidades mediante acciones de desarrollo trazables.', 'desarrollo', '2026-06-01', '2026-10-31', 'PLANIFICADO', 0.0, NULL, 1, '2026-10-17 19:24:22', NULL);

-- accion_plan (11 filas)
INSERT INTO accion_plan (id, plan_id, descripcion, completada, fecha_limite, fecha_creacion) VALUES
(1, 1, 'Programa de liderazgo de equipos ágiles', FALSE, '2026-06-30', '2026-10-17 19:24:22'),
(2, 1, 'Mentoría a dos desarrolladoras junior', TRUE, '2026-09-30', '2026-10-17 19:24:22'),
(3, 1, 'Liderar la migración del pipeline de datos', TRUE, '2026-10-31', '2026-10-17 19:24:22'),
(4, 2, 'Certificación en People Analytics', FALSE, '2026-08-31', '2026-10-17 19:24:22'),
(5, 2, 'Rotación como socio de negocio senior', TRUE, '2026-07-15', '2026-10-17 19:24:22'),
(6, 2, 'Presentar propuesta de modelo de competencias', TRUE, '2026-05-31', '2026-10-17 19:24:22'),
(7, 3, 'Diplomado en finanzas corporativas', TRUE, '2026-04-30', '2026-10-17 19:24:22'),
(8, 3, 'Automatizar el cierre contable mensual', FALSE, '2026-02-28', '2026-10-17 19:24:22'),
(9, 4, 'Certificación en gestión de cuentas clave', FALSE, '2026-09-30', '2026-10-17 19:24:22'),
(10, 4, 'Presentar plan anual de crecimiento a dirección', FALSE, '2026-11-15', '2026-10-17 19:24:22'),
(11, 5, 'Curso de comunicación efectiva', FALSE, '2026-08-15', '2026-10-17 19:24:22');

-- evaluacion (12 filas)
INSERT INTO evaluacion (id, colaborador_id, configuracion_id, periodo, fecha, version_modelo, estado, ejecutado_por_id) VALUES
(1, 1, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(2, 2, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(3, 3, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(4, 4, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(5, 5, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(6, 6, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(7, 7, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(8, 8, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'INCOMPLETA', 1),
(9, 9, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(10, 10, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(11, 11, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'COMPLETA', 1),
(12, 12, 1, '2026-S1', '2026-10-17 19:24:22', 'reglas-v1', 'INCOMPLETA', 1);

-- resultado_evaluacion (12 filas)
INSERT INTO resultado_evaluacion (id, evaluacion_id, puntuacion, clasificacion, cobertura, factores, explicacion, explicacion_origen, fecha_explicacion) VALUES
(1, 1, 89.97, 'ALTO_POTENCIAL', 0.9091, '[{"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 91.02, "normalizado": 1.0, "contribucion": 0.2}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 100.0, "normalizado": 1.0, "contribucion": 0.12}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 92.36, "normalizado": 1.0, "contribucion": 0.12}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 93.49, "normalizado": 1.0, "contribucion": 0.1}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 88.92, "normalizado": 1.0, "contribucion": 0.08}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 94.69, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 92.79, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 96.45, "normalizado": 1.0, "contribucion": 0.05}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 16.9, "normalizado": 0.2817, "contribucion": 0.0197}, {"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 27.18, "normalizado": 0.0, "contribucion": 0.0}]'::json, 'Resumen de la evaluación de Ana Sofía Mendoza Reyes (Tecnología) para el periodo 2026-S1: puntuación global de 90.0/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 91%. Los factores con mayor contribución fueron: Desempeño global (0.2 pts), Competencia de liderazgo (0.1 pts), Cumplimiento de objetivos (0.1 pts), Puntaje promedio de capacitación (0.1 pts), Competencia de comunicación (0.1 pts). La clasificación resultante es «Alto Potencial». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(2, 2, 52.02, 'ESTANDAR', 0.9091, '[{"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 84.72, "normalizado": 0.6508, "contribucion": 0.1302}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 82.83, "normalizado": 1.0, "contribucion": 0.1}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 83.92, "normalizado": 0.7719, "contribucion": 0.0618}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 83.22, "normalizado": 0.3945, "contribucion": 0.0394}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 84.37, "normalizado": 0.6178, "contribucion": 0.0371}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 87.81, "normalizado": 0.6073, "contribucion": 0.0304}, {"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 22.43, "normalizado": 0.7252, "contribucion": 0.029}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 77.6, "normalizado": 0.168, "contribucion": 0.0202}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 80.89, "normalizado": 0.1636, "contribucion": 0.0098}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 15.81, "normalizado": 0.0, "contribucion": 0.0}]'::json, 'Resumen de la evaluación de Carlos Emilio Ramírez Soto (Tecnología) para el periodo 2026-S1: puntuación global de 52.0/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 91%. Los factores con mayor contribución fueron: Desempeño global (0.1 pts), Crecimiento de desempeño vs. periodo anterior (0.1 pts), Competencia de comunicación (0.1 pts), Puntaje promedio de capacitación (0.0 pts), Impacto en proyectos organizacionales (0.0 pts). La clasificación resultante es «Estandar». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(3, 3, 11.0, 'ESTANDAR', 1.0, '[{"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 19.68, "normalizado": 1.0, "contribucion": 0.07}, {"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 20.63, "normalizado": 1.0, "contribucion": 0.04}, {"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 72.98, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 75.97, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 72.39, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 67.0, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 78.19, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 76.53, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 74.45, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 74.62, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 70.76, "normalizado": 0.0, "contribucion": 0.0}]'::json, 'Resumen de la evaluación de Lucía Fernanda Ortiz Cruz (Tecnología) para el periodo 2026-S1: puntuación global de 11.0/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 100%. Los factores con mayor contribución fueron: Años de experiencia (normalizado) (0.1 pts), Rotación del equipo a cargo (0.0 pts), Desempeño global (0.0 pts), Crecimiento de desempeño vs. periodo anterior (0.0 pts), Competencia de liderazgo (0.0 pts). La clasificación resultante es «Estandar». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(4, 4, 2.22, 'ESTANDAR', 0.9091, '[{"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 17.95, "normalizado": 0.5, "contribucion": 0.02}, {"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 80.16, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 85.23, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 82.12, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 79.64, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 77.46, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 77.85, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 17.0, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 83.18, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 76.83, "normalizado": 0.0, "contribucion": 0.0}]'::json, 'Resumen de la evaluación de Diego Alejandro Torres Lima (Recursos Humanos) para el periodo 2026-S1: puntuación global de 2.2/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 91%. Los factores con mayor contribución fueron: Rotación del equipo a cargo (0.0 pts), Desempeño global (0.0 pts), Crecimiento de desempeño vs. periodo anterior (0.0 pts), Competencia de liderazgo (0.0 pts), Competencia de comunicación (0.0 pts). La clasificación resultante es «Estandar». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(5, 5, 94.79, 'ALTO_POTENCIAL', 0.9091, '[{"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 92.77, "normalizado": 1.0, "contribucion": 0.2}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 90.71, "normalizado": 1.0, "contribucion": 0.12}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 96.2, "normalizado": 1.0, "contribucion": 0.12}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 91.79, "normalizado": 1.0, "contribucion": 0.1}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 88.24, "normalizado": 1.0, "contribucion": 0.08}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 23.87, "normalizado": 1.0, "contribucion": 0.07}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 96.36, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 94.84, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 96.97, "normalizado": 0.5, "contribucion": 0.05}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 98.24, "normalizado": 1.0, "contribucion": 0.05}]'::json, 'Resumen de la evaluación de María José Vargas Nieto (Recursos Humanos) para el periodo 2026-S1: puntuación global de 94.8/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 91%. Los factores con mayor contribución fueron: Desempeño global (0.2 pts), Competencia de liderazgo (0.1 pts), Cumplimiento de objetivos (0.1 pts), Crecimiento de desempeño vs. periodo anterior (0.1 pts), Competencia de comunicación (0.1 pts). La clasificación resultante es «Alto Potencial». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(6, 6, 4.55, 'ESTANDAR', 0.9091, '[{"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 17.38, "normalizado": 1.0, "contribucion": 0.04}, {"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 74.05, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 67.78, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 64.75, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 74.78, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 68.97, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 65.16, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 65.48, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 13.92, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 71.29, "normalizado": 0.0, "contribucion": 0.0}]'::json, 'Resumen de la evaluación de Jorge Luis Salgado Prieto (Finanzas) para el periodo 2026-S1: puntuación global de 4.5/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 91%. Los factores con mayor contribución fueron: Rotación del equipo a cargo (0.0 pts), Desempeño global (0.0 pts), Crecimiento de desempeño vs. periodo anterior (0.0 pts), Competencia de liderazgo (0.0 pts), Competencia de comunicación (0.0 pts). La clasificación resultante es «Estandar». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(7, 7, 90.0, 'ALTO_POTENCIAL', 1.0, '[{"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 100.0, "normalizado": 1.0, "contribucion": 0.2}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 97.86, "normalizado": 1.0, "contribucion": 0.12}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 93.31, "normalizado": 1.0, "contribucion": 0.1}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 96.97, "normalizado": 1.0, "contribucion": 0.1}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 96.63, "normalizado": 1.0, "contribucion": 0.08}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 21.35, "normalizado": 1.0, "contribucion": 0.07}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 90.71, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 92.07, "normalizado": 0.5, "contribucion": 0.06}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 91.83, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 89.55, "normalizado": 1.0, "contribucion": 0.05}, {"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 28.28, "normalizado": 0.0, "contribucion": 0.0}]'::json, 'Resumen de la evaluación de Valeria Campos Domínguez (Finanzas) para el periodo 2026-S1: puntuación global de 90.0/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 100%. Los factores con mayor contribución fueron: Desempeño global (0.2 pts), Competencia de liderazgo (0.1 pts), Crecimiento de desempeño vs. periodo anterior (0.1 pts), Puntaje promedio de capacitación (0.1 pts), Competencia de comunicación (0.1 pts). La clasificación resultante es «Alto Potencial». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(8, 8, 5.88, 'NO_EVALUABLE', 0.7273, '[{"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 19.77, "normalizado": 1.0, "contribucion": 0.04}, {"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 70.14, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 81.13, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 74.79, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 79.95, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 11.81, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 77.64, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 75.69, "normalizado": 0.0, "contribucion": 0.0}]'::json, NULL, NULL, NULL),
(9, 9, 80.0, 'ALTO_POTENCIAL', 1.0, '[{"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 96.56, "normalizado": 1.0, "contribucion": 0.2}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 96.67, "normalizado": 1.0, "contribucion": 0.12}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 93.79, "normalizado": 1.0, "contribucion": 0.08}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 21.89, "normalizado": 1.0, "contribucion": 0.07}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 91.11, "normalizado": 0.5, "contribucion": 0.06}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 88.14, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 93.96, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 92.73, "normalizado": 0.5, "contribucion": 0.05}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 92.11, "normalizado": 0.5, "contribucion": 0.05}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 86.95, "normalizado": 1.0, "contribucion": 0.05}, {"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 27.07, "normalizado": 0.0, "contribucion": 0.0}]'::json, 'Resumen de la evaluación de Daniela Paola Ríos Castañeda (Comercial) para el periodo 2026-S1: puntuación global de 80.0/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 100%. Los factores con mayor contribución fueron: Desempeño global (0.2 pts), Cumplimiento de objetivos (0.1 pts), Competencia de comunicación (0.1 pts), Años de experiencia (normalizado) (0.1 pts), Competencia de liderazgo (0.1 pts). La clasificación resultante es «Alto Potencial». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(10, 10, 37.91, 'ESTANDAR', 0.9091, '[{"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 76.2, "normalizado": 0.8604, "contribucion": 0.1032}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 77.52, "normalizado": 1.0, "contribucion": 0.1}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 72.97, "normalizado": 1.0, "contribucion": 0.08}, {"codigo": "ROTACION_EQUIPO", "nombre": "Rotaci\u00f3n del equipo a cargo", "tipo": "organizacional", "peso": 0.04, "valor": 14.95, "normalizado": 0.5, "contribucion": 0.02}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 70.25, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 78.74, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 74.27, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 9.91, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 69.85, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 72.54, "normalizado": 0.0, "contribucion": 0.0}]'::json, 'Resumen de la evaluación de Fernando Miguel Ávila Santos (Operaciones) para el periodo 2026-S1: puntuación global de 37.9/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 91%. Los factores con mayor contribución fueron: Competencia de liderazgo (0.1 pts), Crecimiento de desempeño vs. periodo anterior (0.1 pts), Competencia de comunicación (0.1 pts), Rotación del equipo a cargo (0.0 pts), Competencia de colaboración (0.0 pts). La clasificación resultante es «Estandar». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(11, 11, 98.97, 'ALTO_POTENCIAL', 0.8182, '[{"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 84.89, "normalizado": 1.0, "contribucion": 0.2}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 77.61, "normalizado": 1.0, "contribucion": 0.12}, {"codigo": "CUMPLIMIENTO_OBJETIVOS", "nombre": "Cumplimiento de objetivos", "tipo": "objetivo", "peso": 0.12, "valor": 85.87, "normalizado": 1.0, "contribucion": 0.12}, {"codigo": "PUNTAJE_CAPACITACION", "nombre": "Puntaje promedio de capacitaci\u00f3n", "tipo": "capacitacion", "peso": 0.1, "valor": 79.61, "normalizado": 1.0, "contribucion": 0.1}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 76.54, "normalizado": 0.9089, "contribucion": 0.0909}, {"codigo": "ANIOS_EXPERIENCIA", "nombre": "A\u00f1os de experiencia (normalizado)", "tipo": "experiencia", "peso": 0.07, "valor": 15.36, "normalizado": 1.0, "contribucion": 0.07}, {"codigo": "COLABORACION", "nombre": "Competencia de colaboraci\u00f3n", "tipo": "competencia", "peso": 0.06, "valor": 78.32, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "IMPACTO_PROYECTOS", "nombre": "Impacto en proyectos organizacionales", "tipo": "organizacional", "peso": 0.06, "valor": 84.97, "normalizado": 1.0, "contribucion": 0.06}, {"codigo": "CURSOS_APROBADOS", "nombre": "Cursos aprobados (normalizado 0-100)", "tipo": "capacitacion", "peso": 0.05, "valor": 83.4, "normalizado": 1.0, "contribucion": 0.05}]'::json, 'Resumen de la evaluación de Regina Ocampo Ruiz (Operaciones) para el periodo 2026-S1: puntuación global de 99.0/100 frente a un umbral HiPo de 75, con una cobertura de datos válidos del 82%. Los factores con mayor contribución fueron: Desempeño global (0.2 pts), Competencia de liderazgo (0.1 pts), Cumplimiento de objetivos (0.1 pts), Puntaje promedio de capacitación (0.1 pts), Crecimiento de desempeño vs. periodo anterior (0.1 pts). La clasificación resultante es «Alto Potencial». Este resultado es un insumo de apoyo generado con la versión reglas-v1 del modelo y debe ser revisado por un usuario autorizado antes de tomar decisiones.', 'local_determinista', '2026-10-17 19:24:22.529128'),
(12, 12, 0.0, 'NO_EVALUABLE', 0.3636, '[{"codigo": "DESEMPENO_GLOBAL", "nombre": "Desempe\u00f1o global", "tipo": "desempeno", "peso": 0.2, "valor": 64.69, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "CRECIMIENTO_DESEMPENO", "nombre": "Crecimiento de desempe\u00f1o vs. periodo anterior", "tipo": "desempeno", "peso": 0.1, "valor": 66.76, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "LIDERAZGO", "nombre": "Competencia de liderazgo", "tipo": "competencia", "peso": 0.12, "valor": 67.51, "normalizado": 0.0, "contribucion": 0.0}, {"codigo": "COMUNICACION", "nombre": "Competencia de comunicaci\u00f3n", "tipo": "competencia", "peso": 0.08, "valor": 59.34, "normalizado": 0.0, "contribucion": 0.0}]'::json, NULL, NULL, NULL);

-- auditoria (1 filas)
INSERT INTO auditoria (id, usuario_id, usuario_nombre, accion, recurso, detalle, fecha_hora) VALUES
(1, 1, 'Administrador del Sistema', 'evaluacion.ejecutar', 'periodo:2026-S1/config:v1', '{"periodo": "2026-S1", "configuracion_version": 1, "total": 12, "completos": 10, "incompletos": 2, "version_modelo": "reglas-v1"}'::json, '2026-10-17 19:24:22');

-- =========================== 3) SECUENCIAS ============================
-- Sincroniza las secuencias SERIAL con los ids insertados.
SELECT setval(pg_get_serial_sequence('permiso', 'id'), (SELECT COALESCE(MAX(id), 1) FROM permiso));
SELECT setval(pg_get_serial_sequence('rol', 'id'), (SELECT COALESCE(MAX(id), 1) FROM rol));
SELECT setval(pg_get_serial_sequence('usuario', 'id'), (SELECT COALESCE(MAX(id), 1) FROM usuario));
SELECT setval(pg_get_serial_sequence('colaborador', 'id'), (SELECT COALESCE(MAX(id), 1) FROM colaborador));
SELECT setval(pg_get_serial_sequence('indicador', 'id'), (SELECT COALESCE(MAX(id), 1) FROM indicador));
SELECT setval(pg_get_serial_sequence('area_evaluacion', 'id'), (SELECT COALESCE(MAX(id), 1) FROM area_evaluacion));
SELECT setval(pg_get_serial_sequence('configuracion_evaluacion', 'id'), (SELECT COALESCE(MAX(id), 1) FROM configuracion_evaluacion));
SELECT setval(pg_get_serial_sequence('medicion_indicador', 'id'), (SELECT COALESCE(MAX(id), 1) FROM medicion_indicador));
SELECT setval(pg_get_serial_sequence('plan_desarrollo', 'id'), (SELECT COALESCE(MAX(id), 1) FROM plan_desarrollo));
SELECT setval(pg_get_serial_sequence('accion_plan', 'id'), (SELECT COALESCE(MAX(id), 1) FROM accion_plan));
SELECT setval(pg_get_serial_sequence('evaluacion', 'id'), (SELECT COALESCE(MAX(id), 1) FROM evaluacion));
SELECT setval(pg_get_serial_sequence('resultado_evaluacion', 'id'), (SELECT COALESCE(MAX(id), 1) FROM resultado_evaluacion));
SELECT setval(pg_get_serial_sequence('auditoria', 'id'), (SELECT COALESCE(MAX(id), 1) FROM auditoria));

COMMIT;
