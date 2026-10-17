-- Esquema PostgreSQL del Sistema HiPo.

BEGIN;


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

COMMIT;
