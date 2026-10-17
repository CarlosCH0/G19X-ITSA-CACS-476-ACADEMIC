# -*- coding: utf-8 -*-
"""Gestión de indicadores y mediciones (RF-04, RN-01, RN-02)."""
import csv
import io
import math
import zipfile
from datetime import date, datetime

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils.exceptions import InvalidFileException

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import UserContext
from app.models import Colaborador, Indicador, MedicionIndicador, Validez
from app.schemas import IndicadorCreate, IndicadorUpdate, MedicionBulkRequest
from app.services import auditoria_service


def listar_indicadores(db: Session, solo_activos: bool = False) -> list[Indicador]:
    consulta = select(Indicador).order_by(Indicador.tipo, Indicador.codigo)
    if solo_activos:
        consulta = consulta.where(Indicador.activo.is_(True))
    return list(db.scalars(consulta))


def crear_indicador(db: Session, usuario: UserContext, datos: IndicadorCreate) -> Indicador:
    if db.scalars(select(Indicador).where(Indicador.codigo == datos.codigo)).first():
        raise ValueError(f"Ya existe el indicador {datos.codigo}")
    ind = Indicador(**datos.model_dump())
    db.add(ind)
    db.flush()
    auditoria_service.registrar(
        db, accion="indicador.crear", recurso=f"indicador:{ind.codigo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
    )
    db.commit()
    db.refresh(ind)
    return ind


def actualizar_indicador(
    db: Session, usuario: UserContext, indicador_id: int, datos: IndicadorUpdate
) -> Indicador | None:
    ind = db.get(Indicador, indicador_id)
    if ind is None:
        return None
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(ind, campo, valor)
    auditoria_service.registrar(
        db, accion="indicador.actualizar", recurso=f"indicador:{ind.codigo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
    )
    db.commit()
    db.refresh(ind)
    return ind


def registrar_mediciones(
    db: Session, usuario: UserContext, peticion: MedicionBulkRequest
) -> list[MedicionIndicador]:
    """Carga masiva por colaborador/periodo; upsert sobre la combinación única."""
    if db.get(Colaborador, peticion.colaborador_id) is None:
        raise ValueError("Colaborador inexistente")
    existentes = {
        m.indicador_id: m
        for m in db.scalars(
            select(MedicionIndicador).where(
                MedicionIndicador.colaborador_id == peticion.colaborador_id,
                MedicionIndicador.periodo == peticion.periodo,
            )
        )
    }
    indicadores = {
        indicador.id: indicador
        for indicador in db.scalars(
            select(Indicador).where(
                Indicador.id.in_([entrada.indicador_id for entrada in peticion.mediciones])
            )
        )
    }
    for entrada in peticion.mediciones:
        indicador = indicadores.get(entrada.indicador_id)
        if indicador is None:
            raise ValueError(f"Indicador inexistente: {entrada.indicador_id}")
        error_rango = _validar_rango_medicion(indicador.codigo, entrada.valor)
        if error_rango:
            raise ValueError(f"{indicador.nombre}: {error_rango}")

    resultado: list[MedicionIndicador] = []
    for entrada in peticion.mediciones:
        m = existentes.get(entrada.indicador_id)
        if m:  # actualiza valor y baja validez a pendiente (RN-01: revalidar)
            m.valor = entrada.valor
            m.validez = entrada.validez
            m.comentario = entrada.comentario
        else:
            m = MedicionIndicador(
                colaborador_id=peticion.colaborador_id,
                indicador_id=entrada.indicador_id,
                periodo=peticion.periodo,
                valor=entrada.valor,
                validez=entrada.validez,
                comentario=entrada.comentario,
            )
            db.add(m)
        resultado.append(m)
    auditoria_service.registrar(
        db, accion="medicion.cargar", recurso=f"colaborador:{peticion.colaborador_id}/{peticion.periodo}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={"cantidad": len(peticion.mediciones), "periodo": peticion.periodo},
    )
    db.commit()
    return resultado


def cambiar_validez(
    db: Session, usuario: UserContext, medicion_id: int, validez: Validez, comentario: str = ""
) -> MedicionIndicador | None:
    """Validación/invalidez de una medición (RN-01, RN-02)."""
    m = db.get(MedicionIndicador, medicion_id)
    if m is None:
        return None
    m.validez = validez
    if comentario:
        m.comentario = comentario
    auditoria_service.registrar(
        db, accion="medicion.validez", recurso=f"medicion:{medicion_id}",
        usuario_id=usuario.id, usuario_nombre=usuario.nombre,
        detalle={"validez": validez.value, "periodo": m.periodo},
    )
    db.commit()
    db.refresh(m)
    return m


def mediciones_de_colaborador(
    db: Session, colaborador_id: int, periodo: str | None = None
) -> list[MedicionIndicador]:
    consulta = select(MedicionIndicador).where(
        MedicionIndicador.colaborador_id == colaborador_id
    )
    if periodo:
        consulta = consulta.where(MedicionIndicador.periodo == periodo)
    return list(db.scalars(consulta.order_by(MedicionIndicador.periodo.desc())))


def periodos_disponibles(db: Session) -> list[str]:
    return list(
        db.scalars(
            select(MedicionIndicador.periodo)
            .distinct()
            .order_by(MedicionIndicador.periodo.desc())
        )
    )


# ------------------------------------------------------------------
# Carga masiva desde CSV para importar y validar mediciones.
# ------------------------------------------------------------------
COLUMNAS_CSV = ["colaborador_codigo", "indicador_codigo", "periodo", "valor", "validez"]
INDICADORES_NO_ESCALADOS = {"ANIOS_EXPERIENCIA", "ROTACION_EQUIPO"}


def _validar_rango_medicion(codigo: str, valor: float) -> str | None:
    if not math.isfinite(valor):
        return "El valor debe ser un número finito."
    if codigo in INDICADORES_NO_ESCALADOS:
        return "El valor no puede ser negativo." if valor < 0 else None
    if not 0 <= valor <= 100:
        return "El valor debe estar entre 0 y 100."
    return None


def plantilla_csv(db: Session) -> str:
    """Plantilla de ejemplo con colaboradores e indicadores existentes."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(COLUMNAS_CSV)
    codigo_colab = db.scalar(select(Colaborador.codigo).limit(1)) or "COL-001"
    codigos_ind = list(db.scalars(select(Indicador.codigo).limit(3)))
    for i, cod in enumerate(codigos_ind or ["DESEMPENO_GLOBAL"]):
        writer.writerow([codigo_colab, cod, "2026-S2", 90.0 + i, "valida"])
    return buffer.getvalue()


def plantilla_xlsx() -> bytes:
    """Genera una plantilla de Excel formateada para cargar mediciones."""
    libro = Workbook()
    instrucciones = libro.active
    instrucciones.title = "Instrucciones"
    mediciones = libro.create_sheet("Mediciones")

    azul = "17365D"
    azul_medio = "1F4E78"
    turquesa = "0F766E"
    fondo = "F3F7FB"
    texto = "24364B"
    gris = "5B6B7A"
    blanco = "FFFFFF"
    borde = Side(style="thin", color="D9E2F0")

    instrucciones.sheet_view.showGridLines = False
    instrucciones.merge_cells("A1:F2")
    titulo = instrucciones["A1"]
    titulo.value = "PLANTILLA DE CARGA MASIVA"
    titulo.fill = PatternFill("solid", fgColor=azul)
    titulo.font = Font(name="Aptos Display", size=22, bold=True, color=blanco)
    titulo.alignment = Alignment(vertical="center", indent=1)
    for row in instrucciones["A1:F2"]:
        for celda in row:
            celda.fill = PatternFill("solid", fgColor=azul)
    instrucciones.row_dimensions[1].height = 30
    instrucciones.row_dimensions[2].height = 22

    instrucciones.merge_cells("A3:F3")
    instrucciones["A3"] = "Sistema HiPo · Importación de mediciones de colaboradores"
    instrucciones["A3"].font = Font(name="Aptos", size=11, italic=True, color=gris)
    instrucciones["A3"].alignment = Alignment(indent=1, vertical="center")
    instrucciones.row_dimensions[3].height = 26

    instrucciones.merge_cells("A5:F5")
    instrucciones["A5"] = "CÓMO COMPLETAR Y CARGAR EL ARCHIVO"
    instrucciones["A5"].fill = PatternFill("solid", fgColor=turquesa)
    instrucciones["A5"].font = Font(name="Aptos", size=11, bold=True, color=blanco)
    instrucciones["A5"].alignment = Alignment(indent=1, vertical="center")
    for celda in instrucciones[5]:
        celda.fill = PatternFill("solid", fgColor=turquesa)
    instrucciones.row_dimensions[5].height = 24

    pasos = [
        ("01", "Abre la pestaña Mediciones y agrega una medición por fila, debajo de los encabezados."),
        ("02", "Respeta los nombres y el orden de las cinco columnas. No cambies ni elimines los encabezados."),
        ("03", "Usa códigos de colaboradores activos e indicadores del catálogo de HiPo."),
        ("04", "En valor, captura puntuaciones de 0 a 100. Años de experiencia y rotación aceptan cantidades no negativas."),
        ("05", "Guarda el archivo como .xlsx, súbelo en Carga masiva y elige «Solo validar» antes de registrar."),
    ]
    for fila, (numero, texto_paso) in enumerate(pasos, start=6):
        instrucciones.cell(fila, 1, numero)
        instrucciones.cell(fila, 1).font = Font(name="Aptos", size=11, bold=True, color=turquesa)
        instrucciones.merge_cells(start_row=fila, start_column=2, end_row=fila, end_column=6)
        celda = instrucciones.cell(fila, 2, texto_paso)
        celda.font = Font(name="Aptos", size=10, color=texto)
        celda.alignment = Alignment(wrap_text=True, vertical="center")
        instrucciones.row_dimensions[fila].height = 32

    inicio_campos = 13
    instrucciones.merge_cells(start_row=inicio_campos, start_column=1, end_row=inicio_campos, end_column=6)
    instrucciones.cell(inicio_campos, 1, "COLUMNAS REQUERIDAS")
    instrucciones.cell(inicio_campos, 1).fill = PatternFill("solid", fgColor=azul_medio)
    instrucciones.cell(inicio_campos, 1).font = Font(name="Aptos", size=11, bold=True, color=blanco)
    instrucciones.cell(inicio_campos, 1).alignment = Alignment(indent=1, vertical="center")
    for celda in instrucciones[inicio_campos]:
        celda.fill = PatternFill("solid", fgColor=azul_medio)
    instrucciones.row_dimensions[inicio_campos].height = 24

    descripciones = [
        ("colaborador_codigo", "Código del colaborador activo, por ejemplo COL-001."),
        ("indicador_codigo", "Código exacto del indicador, por ejemplo LIDERAZGO."),
        ("periodo", "Identificador de periodo, por ejemplo 2026-S2."),
        ("valor", "Valor numérico; puntuaciones de 0 a 100."),
        ("validez", "valida, pendiente o invalida. Si queda vacío, se considera pendiente."),
    ]
    for fila, (campo, descripcion) in enumerate(descripciones, start=inicio_campos + 1):
        instrucciones.cell(fila, 1, campo)
        instrucciones.cell(fila, 1).font = Font(name="Aptos", size=10, bold=True, color=azul_medio)
        instrucciones.merge_cells(start_row=fila, start_column=2, end_row=fila, end_column=6)
        instrucciones.cell(fila, 2, descripcion)
        instrucciones.cell(fila, 2).font = Font(name="Aptos", size=10, color=texto)
        instrucciones.cell(fila, 2).alignment = Alignment(wrap_text=True, vertical="center")
        for columna in range(1, 7):
            celda = instrucciones.cell(fila, columna)
            celda.fill = PatternFill("solid", fgColor=blanco if fila % 2 else fondo)
            celda.border = Border(bottom=borde)
        instrucciones.row_dimensions[fila].height = 25

    instrucciones.merge_cells("A20:F21")
    instrucciones["A20"] = (
        "Importante: la validación previa no registra cambios. Si una fila ya existe para el mismo "
        "colaborador, indicador y periodo, volver a cargarla actualiza el valor y la deja pendiente de revisión."
    )
    instrucciones["A20"].fill = PatternFill("solid", fgColor="FFF4D6")
    instrucciones["A20"].font = Font(name="Aptos", size=10, color="7A5410")
    instrucciones["A20"].alignment = Alignment(wrap_text=True, vertical="center", indent=1)
    for row in instrucciones["A20:F21"]:
        for celda in row:
            celda.fill = PatternFill("solid", fgColor="FFF4D6")
    instrucciones.row_dimensions[20].height = 28
    instrucciones.row_dimensions[21].height = 22
    for columna, ancho in {"A": 25, "B": 23, "C": 16, "D": 16, "E": 16, "F": 16}.items():
        instrucciones.column_dimensions[columna].width = ancho

    mediciones.sheet_view.showGridLines = False
    mediciones.freeze_panes = "A2"
    mediciones.sheet_properties.pageSetUpPr.fitToPage = True
    mediciones.page_setup.orientation = "landscape"
    mediciones.page_setup.fitToWidth = 1
    mediciones.page_setup.fitToHeight = 0
    mediciones.sheet_properties.tabColor = turquesa
    encabezados = [
        ("colaborador_codigo", "Código del colaborador activo. Ejemplo: COL-001."),
        ("indicador_codigo", "Código existente del indicador. Ejemplo: LIDERAZGO."),
        ("periodo", "Periodo de medición. Ejemplo: 2026-S2."),
        ("valor", "Puntuaciones de 0 a 100; experiencia y rotación no pueden ser negativas."),
        ("validez", "valida, pendiente o invalida. Vacío equivale a pendiente."),
    ]
    for columna, (nombre, comentario) in enumerate(encabezados, start=1):
        celda = mediciones.cell(1, columna, nombre)
        celda.fill = PatternFill("solid", fgColor=azul)
        celda.font = Font(name="Aptos", size=10, bold=True, color=blanco)
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celda.border = Border(bottom=Side(style="medium", color=turquesa))
        celda.comment = Comment(comentario, "HiPo")
    mediciones.row_dimensions[1].height = 32
    for fila in range(2, 102):
        for columna in range(1, len(COLUMNAS_CSV) + 1):
            celda = mediciones.cell(fila, columna)
            celda.fill = PatternFill("solid", fgColor=blanco if fila % 2 == 0 else fondo)
            celda.font = Font(name="Aptos", size=10, color=texto)
            celda.border = Border(bottom=borde)
            celda.alignment = Alignment(vertical="center")
        mediciones.row_dimensions[fila].height = 21
    for columna, ancho in {"A": 24, "B": 30, "C": 21, "D": 16, "E": 18}.items():
        mediciones.column_dimensions[columna].width = ancho
    mediciones.auto_filter.ref = "A1:E101"

    validez = DataValidation(type="list", formula1='"valida,pendiente,invalida"', allow_blank=True)
    validez.error = "Elige valida, pendiente o invalida."
    validez.errorTitle = "Validez no reconocida"
    validez.prompt = "Selecciona el estado de revisión de esta medición."
    validez.promptTitle = "Estado de validez"
    mediciones.add_data_validation(validez)
    validez.add("E2:E101")

    valor = DataValidation(
        type="custom",
        formula1='=OR(AND($B2="ANIOS_EXPERIENCIA",$D2>=0),'
        'AND($B2="ROTACION_EQUIPO",$D2>=0),'
        'AND($B2<>"ANIOS_EXPERIENCIA",$B2<>"ROTACION_EQUIPO",$D2>=0,$D2<=100))',
        allow_blank=True,
    )
    valor.error = "Usa un valor no negativo; las puntuaciones deben estar entre 0 y 100."
    valor.errorTitle = "Valor fuera de rango"
    mediciones.add_data_validation(valor)
    valor.add("D2:D101")

    libro.active = 0
    salida = io.BytesIO()
    libro.save(salida)
    libro.close()
    return salida.getvalue()


def xlsx_a_csv(contenido: bytes) -> str:
    """Convierte la hoja Mediciones de un archivo XLSX a CSV para compartir validación."""
    try:
        libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except (InvalidFileException, zipfile.BadZipFile, OSError, ValueError, KeyError) as exc:
        raise ValueError("El archivo Excel no es válido o está dañado.") from exc

    try:
        if "Mediciones" not in libro.sheetnames:
            raise ValueError("El archivo Excel debe incluir una hoja llamada «Mediciones».")
        hoja = libro["Mediciones"]
        salida = io.StringIO()
        escritor = csv.writer(salida, delimiter=";", lineterminator="\n")
        for fila in hoja.iter_rows(values_only=True):
            if not any(valor is not None and str(valor).strip() for valor in fila):
                continue
            celdas = []
            for valor in fila:
                if isinstance(valor, (datetime, date)):
                    celdas.append(valor.isoformat())
                elif isinstance(valor, float) and valor.is_integer():
                    celdas.append(str(int(valor)))
                else:
                    celdas.append("" if valor is None else str(valor).strip())
            escritor.writerow(celdas)
        return salida.getvalue()
    finally:
        libro.close()


def cargar_mediciones_csv(
    db: Session, usuario: UserContext, contenido: str, validar_solo: bool = False
) -> dict:
    """Procesa un CSV de mediciones con reporte de validación (RN-01).

    Columnas esperadas (separadas por ';'): colaborador_codigo, indicador_codigo,
    periodo, valor, validez (valida|pendiente|invalida). Solo las filas válidas
    se registran; las demás se reportan con el motivo del rechazo.
    """
    lector = csv.reader(io.StringIO(contenido.strip()), delimiter=";")
    filas = [f for f in lector if any(c.strip() for c in f)]
    if not filas:
        raise ValueError("El archivo CSV está vacío")

    encabezado = [c.strip().lower() for c in filas[0]]
    if encabezado != COLUMNAS_CSV:
        raise ValueError(
            "Encabezado inválido. Se esperaba: " + ";".join(COLUMNAS_CSV)
        )

    colaboradores = {
        c.codigo: c for c in db.scalars(select(Colaborador).where(Colaborador.estado.is_(True)))
    }
    indicadores = {
        i.codigo: i for i in db.scalars(select(Indicador).where(Indicador.activo.is_(True)))
    }

    aceptadas: list[dict] = []
    rechazadas: list[dict] = []
    for numero, fila in enumerate(filas[1:], start=2):
        if len(fila) < 4:
            rechazadas.append({"linea": numero, "motivo": "Columnas insuficientes"})
            continue
        codigo_colab = fila[0].strip()
        codigo_ind = fila[1].strip().upper()
        periodo = fila[2].strip()
        try:
            valor = float(fila[3].strip().replace(",", "."))
        except ValueError:
            rechazadas.append({"linea": numero, "motivo": f"Valor no numérico: '{fila[3].strip()}'"})
            continue
        validez_txt = (fila[4].strip().lower() if len(fila) > 4 and fila[4].strip() else "pendiente")

        if codigo_colab not in colaboradores:
            rechazadas.append({"linea": numero, "motivo": f"Colaborador inexistente: {codigo_colab}"})
            continue
        if codigo_ind not in indicadores:
            rechazadas.append({"linea": numero, "motivo": f"Indicador inexistente: {codigo_ind}"})
            continue
        if not periodo:
            rechazadas.append({"linea": numero, "motivo": "Periodo vacío"})
            continue
        try:
            validez = Validez(validez_txt)
        except ValueError:
            rechazadas.append({"linea": numero, "motivo": f"Validez inválida: '{validez_txt}'"})
            continue

        error_rango = _validar_rango_medicion(codigo_ind, valor)
        if error_rango:
            rechazadas.append({"linea": numero, "motivo": error_rango})
            continue

        aceptadas.append(
            {
                "linea": numero,
                "colaborador": colaboradores[codigo_colab],
                "indicador": indicadores[codigo_ind],
                "periodo": periodo,
                "valor": valor,
                "validez": validez,
            }
        )

    registradas = 0
    if not validar_solo and aceptadas:
        existentes = {
            (m.colaborador_id, m.indicador_id, m.periodo): m
            for m in db.scalars(select(MedicionIndicador))
        }
        for item in aceptadas:
            clave = (
                item["colaborador"].id,
                item["indicador"].id,
                item["periodo"],
            )
            m = existentes.get(clave)
            if m:  # RN-01: recargar un valor lo regresa a PENDIENTE
                m.valor = item["valor"]
                m.validez = item["validez"]
            else:
                m = MedicionIndicador(
                    colaborador_id=item["colaborador"].id,
                    indicador_id=item["indicador"].id,
                    periodo=item["periodo"],
                    valor=item["valor"],
                    validez=item["validez"],
                    comentario=f"Carga CSV por {usuario.nombre}",
                )
                db.add(m)
                existentes[clave] = m
            registradas += 1
        auditoria_service.registrar(
            db, accion="medicion.carga_csv", recurso="mediciones:csv",
            usuario_id=usuario.id, usuario_nombre=usuario.nombre,
            detalle={"aceptadas": registradas, "rechazadas": len(rechazadas)},
        )
        db.commit()

    return {
        "modo": "validacion" if validar_solo else "carga",
        "total_filas": len(filas) - 1,
        "aceptadas": len(aceptadas),
        "rechazadas": len(rechazadas),
        "registradas": registradas,
        "detalle_rechazos": rechazadas[:50],
    }
