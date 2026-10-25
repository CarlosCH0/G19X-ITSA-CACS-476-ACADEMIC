import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client.js'

const EJEMPLO_CSV = `colaborador_codigo;indicador_codigo;periodo;valor;validez
COL-001;DESEMPENO_GLOBAL;2026-S2;92.5;valida
COL-001;LIDERAZGO;2026-S2;88.0;pendiente`
const COLUMNAS_CSV = ['colaborador_codigo', 'indicador_codigo', 'periodo', 'valor', 'validez']

export default function CargaDatos() {
  const [contenido, setContenido] = useState('')
  const [reporte, setReporte] = useState(null)
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [cargando, setCargando] = useState(false)
  const [archivoExcel, setArchivoExcel] = useState(null)
  const entradaArchivo = useRef(null)

  const leerArchivo = (archivo) => {
    if (!archivo) return
    const nombre = archivo.name.toLowerCase()
    if (!nombre.endsWith('.csv') && !nombre.endsWith('.xlsx')) {
      setError('Selecciona un archivo con extensión .csv o .xlsx')
      return
    }
    if (nombre.endsWith('.xlsx')) {
      setArchivoExcel(archivo)
      setContenido('')
      setReporte(null)
      setError('')
      setAviso(`Archivo Excel ${archivo.name} listo. Valida el contenido antes de registrarlo.`)
      return
    }
    setArchivoExcel(null)
    const lector = new FileReader()
    lector.onload = () => {
      setContenido(String(lector.result || ''))
      setReporte(null)
      setError('')
      setAviso(`Archivo ${archivo.name} cargado. Revisa el contenido y valida antes de registrar.`)
    }
    lector.onerror = () => setError('No se pudo leer el archivo')
    lector.readAsText(archivo, 'utf-8')
  }

  const procesar = async (validarSolo) => {
    if (!contenido.trim() && !archivoExcel) {
      setError('Carga un archivo CSV o Excel, o pega el contenido de un CSV.')
      return
    }
    if (!archivoExcel) {
      const csv = contenido.replace(/^\uFEFF/, '')
      const encabezado = csv.split(/\r?\n/).find((linea) => linea.trim())
      const columnas = encabezado?.split(';').map((columna) => columna.trim().toLowerCase())
      if (!columnas || columnas.length !== COLUMNAS_CSV.length
        || columnas.some((columna, indice) => columna !== COLUMNAS_CSV[indice])) {
        setError(`Encabezado CSV inválido. Usa estas columnas en este orden: ${COLUMNAS_CSV.join(';')}.`)
        return
      }
    }
    setCargando(true)
    setError('')
    setAviso('')
    try {
      let resultado
      if (archivoExcel) {
        const formulario = new FormData()
        formulario.append('archivo', archivoExcel)
        formulario.append('validar_solo', String(validarSolo))
        resultado = await api.postArchivo('/api/indicadores/carga-xlsx', formulario)
      } else {
        resultado = await api.post('/api/indicadores/carga-csv', {
          contenido: contenido.replace(/^\uFEFF/, ''), validar_solo: validarSolo,
        })
      }
      setReporte(resultado)
      if (!validarSolo) setAviso(`Carga aplicada: ${resultado.registradas} mediciones registradas.`)
    } catch (e) { setError(e.message) } finally { setCargando(false) }
  }

  const descargarPlantilla = async (formato) => {
    setError('')
    try {
      await api.descargarCsv(`/api/indicadores/plantilla-${formato}`)
    } catch (e) { setError(e.message) }
  }

  const lineas = contenido ? contenido.trim().split('\n').length : 0

  return (
    <div>
      <h1 className="titulo">Carga masiva de mediciones</h1>
      <p className="subtitulo">
        Importa mediciones desde Excel (.xlsx) o CSV. Nada se guarda sin revisión: cada fila se valida
        y solo se aceptan colaboradores activos e indicadores existentes.
      </p>
      {error && <div className="error">{error}</div>}
      {aviso && <div className="aviso">{aviso}</div>}

      <div className="grid-2">
        <div className="panel">
          <h2>1 · Selecciona el archivo</h2>
          <div className="zona-carga" onClick={() => entradaArchivo.current?.click()}
               onDragOver={(e) => e.preventDefault()}
               onDrop={(e) => { e.preventDefault(); leerArchivo(e.dataTransfer.files?.[0]) }}>
            <input ref={entradaArchivo} type="file" accept=".csv,.xlsx" style={{ display: 'none' }}
                   onChange={(e) => { leerArchivo(e.target.files?.[0]); e.currentTarget.value = '' }} />
            <div style={{ fontSize: 34 }}>📄</div>
            <div><b>Arrastra un archivo Excel o CSV</b> o haz clic para seleccionarlo</div>
            <div style={{ fontSize: 12, color: 'var(--gris-500)' }}>
              Excel .xlsx con formato profesional o CSV separado por «;»
            </div>
          </div>
          <div className="botones" style={{ marginTop: 12 }}>
            <button onClick={() => descargarPlantilla('xlsx')}>⬇ Descargar plantilla Excel</button>
            <button className="secundario" onClick={() => descargarPlantilla('csv')}>Descargar CSV</button>
            <button className="secundario" onClick={() => { setArchivoExcel(null); setContenido(EJEMPLO_CSV) }}>Usar ejemplo CSV</button>
          </div>

          <h2 style={{ marginTop: 18 }}>2 · Revisa el contenido</h2>
          {archivoExcel && (
            <div className="aviso">Excel seleccionado: <b>{archivoExcel.name}</b>. Usa «Solo validar» para revisar las filas sin registrarlas.</div>
          )}
          <textarea
            className="csv-editor"
            rows={10}
            spellCheck={false}
            placeholder={EJEMPLO_CSV}
            value={contenido}
            onChange={(e) => { setContenido(e.target.value); setArchivoExcel(null); setReporte(null) }}
          />
          <p className="subtitulo">
            {archivoExcel ? 'El archivo Excel se procesa directamente, sin convertirlo a texto.' : lineas > 0 ? `${lineas} líneas (incluye encabezado)` : 'Sin contenido'}
          </p>

          <div className="botones">
            <button className="secundario" disabled={(!contenido && !archivoExcel) || cargando}
                    onClick={() => procesar(true)}>🔍 Solo validar</button>
            <button disabled={(!contenido && !archivoExcel) || cargando}
                    onClick={() => procesar(false)}>✔ Validar y registrar</button>
          </div>
        </div>

        <div className="panel">
          <h2>Formato esperado</h2>
          <table className="tabla">
            <thead><tr><th>Columna</th><th>Descripción</th><th>Ejemplo</th></tr></thead>
            <tbody>
              <tr><td><b>colaborador_codigo</b></td><td>Código del colaborador activo</td><td>COL-001</td></tr>
              <tr><td><b>indicador_codigo</b></td><td>Código del indicador</td><td>LIDERAZGO</td></tr>
              <tr><td><b>periodo</b></td><td>Periodo de la medición</td><td>2026-S2</td></tr>
              <tr><td><b>valor</b></td><td>
                Puntuaciones: de 0 a 100. Años de experiencia y rotación: cantidades no negativas.
              </td><td>88.5</td></tr>
              <tr><td><b>validez</b></td><td>valida · pendiente · invalida (opcional, por defecto pendiente)</td><td>valida</td></tr>
            </tbody>
          </table>
          <div className="aviso" style={{ marginTop: 12 }}>
            Si cargas una fila que ya existe (mismo colaborador, indicador y periodo), su valor se
            actualiza y queda <b>PENDIENTE</b> hasta que alguien la valide. Todas las cargas quedan
            en la auditoría.
          </div>
        </div>
      </div>

      {reporte && (
        <div className="panel">
          <h2>
            {reporte.modo === 'validacion' ? 'Resultado de validación (sin registrar)' : 'Resultado de la carga'}
          </h2>
          <div className="tarjetas">
            <div className="tarjeta"><div className="etiqueta">Filas procesadas</div><div className="valor">{reporte.total_filas}</div></div>
            <div className="tarjeta"><div className="etiqueta">Aceptadas</div><div className="valor" style={{ color: 'var(--verde)' }}>{reporte.aceptadas}</div></div>
            <div className="tarjeta"><div className="etiqueta">Rechazadas</div><div className="valor" style={{ color: 'var(--rojo)' }}>{reporte.rechazadas}</div></div>
            <div className="tarjeta"><div className="etiqueta">Registradas</div><div className="valor">{reporte.registradas}</div></div>
          </div>
          {reporte.detalle_rechazos.length > 0 && (
            <>
              <h2 style={{ fontSize: 14 }}>Motivos de rechazo</h2>
              <table className="tabla">
                <thead><tr><th>Línea</th><th>Motivo</th></tr></thead>
                <tbody>
                  {reporte.detalle_rechazos.map((d, i) => (
                    <tr key={i}><td>{d.linea}</td><td>{d.motivo}</td></tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          {reporte.rechazadas === 0 && reporte.aceptadas > 0 && (
            <div className="aviso">Todas las filas son válidas.</div>
          )}
        </div>
      )}
    </div>
  )
}
