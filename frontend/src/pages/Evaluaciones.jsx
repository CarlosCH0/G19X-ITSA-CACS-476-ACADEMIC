import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

const CLAS = {
  alto_potencial: ['et-hipo', 'Alto potencial'],
  en_desarrollo: ['et-desarrollo', 'En desarrollo'],
  estandar: ['et-estandar', 'Estándar'],
  no_evaluable: ['et-noevaluable', 'No evaluable'],
}

export default function Evaluaciones() {
  const { puede } = useAuth()
  const [datos, setDatos] = useState(null)
  const [periodos, setPeriodos] = useState([])
  const [filtros, setFiltros] = useState({ periodo: '', clasificacion: '', area: '' })
  const [pagina, setPagina] = useState(1)
  const [error, setError] = useState('')
  const [ejecutando, setEjecutando] = useState(false)
  const [resumen, setResumen] = useState(null)
  const [modal, setModal] = useState(false)
  const [nuevoPeriodo, setNuevoPeriodo] = useState('')

  const cargar = () => {
    api.get('/api/evaluaciones', { ...filtros, pagina, tamanio: 12 })
      .then(setDatos).catch((e) => setError(e.message))
  }
  useEffect(cargar, [filtros, pagina])
  useEffect(() => { api.get('/api/indicadores/periodos').then(setPeriodos) }, [])

  const ejecutar = async () => {
    if (!nuevoPeriodo) { setError('Indica el periodo a evaluar.'); return }
    setEjecutando(true)
    setError('')
    try {
      const r = await api.post('/api/evaluaciones/ejecutar', { periodo: nuevoPeriodo })
      setResumen(r)
      setModal(false)
      setNuevoPeriodo('')
      setFiltros({ ...filtros, periodo: nuevoPeriodo })
      setPagina(1)
      api.get('/api/indicadores/periodos').then(setPeriodos)
      cargar()
    } catch (e) { setError(e.message) } finally { setEjecutando(false) }
  }

  const paginas = datos ? Math.max(1, Math.ceil(datos.total / datos.tamanio)) : 1

  return (
    <div>
      <h1 className="titulo">Evaluaciones de talento</h1>
      <p className="subtitulo">
        Resultados del proceso de evaluación: cada colaborador recibe una puntuación de 0 a 100 y una
        clasificación. Todo resultado se confirma por una persona antes de usarse en decisiones.
      </p>
      {error && <div className="error">{error}</div>}

      {resumen && (
        <div className="aviso">
          Evaluación terminada para el periodo <b>{resumen.periodo}</b> (criterios v{resumen.configuracion_version},
          modelo {resumen.version_modelo}): se evaluaron {resumen.total_evaluados} colaboradores —{' '}
          {resumen.completos} con datos completos y {resumen.incompletos} con datos incompletos.{' '}
          Resultado: {Object.entries(resumen.por_clasificacion).map(([k, v]) => `${CLAS[k]?.[1] || k}: ${v}`).join(' · ')}
        </div>
      )}

      <div className="filtros">
        <select value={filtros.periodo} onChange={(e) => { setPagina(1); setFiltros({ ...filtros, periodo: e.target.value }) }}>
          <option value="">Todos los periodos</option>
          {periodos.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <select value={filtros.clasificacion} onChange={(e) => { setPagina(1); setFiltros({ ...filtros, clasificacion: e.target.value }) }}>
          <option value="">Todas las clasificaciones</option>
          {Object.entries(CLAS).map(([k, v]) => <option key={k} value={k}>{v[1]}</option>)}
        </select>
        <input placeholder="Área" value={filtros.area}
               onChange={(e) => { setPagina(1); setFiltros({ ...filtros, area: e.target.value }) }} />
        {puede('evaluaciones.ejecutar') && (
          <button onClick={() => setModal(true)}>▶ Ejecutar evaluación</button>
        )}
      </div>

      {modal && (
        <div className="panel">
          <h2>Ejecutar una nueva evaluación</h2>
          <p className="subtitulo">
            El sistema calculará la puntuación de todos los colaboradores activos usando los criterios
            vigentes. Las evaluaciones de otros periodos no cambian.
          </p>
          <div className="filtros">
            <input placeholder="Periodo (ej. 2026-S2)" value={nuevoPeriodo} onChange={(e) => setNuevoPeriodo(e.target.value)} />
            <button onClick={ejecutar} disabled={ejecutando}>{ejecutando ? 'Procesando…' : 'Ejecutar ahora'}</button>
            <button className="secundario" onClick={() => setModal(false)}>Cancelar</button>
          </div>
        </div>
      )}

      <div className="panel">
        <table className="tabla">
          <thead>
            <tr>
              <th>Colaborador</th><th>Área</th><th>Periodo</th><th>Puntuación</th>
              <th>Clasificación</th><th>Revisión</th><th>Modelo</th><th></th>
            </tr>
          </thead>
          <tbody>
            {datos?.items.map((e) => (
              <tr key={e.id}>
                <td>{e.colaborador_nombre}</td>
                <td>{e.area}</td>
                <td>{e.periodo}</td>
                <td><b>{e.puntuacion ?? '—'}</b></td>
                <td><span className={`etiqueta-estado ${CLAS[e.clasificacion]?.[0] || 'et-sin'}`}>
                  {CLAS[e.clasificacion]?.[1] || '—'}
                </span></td>
                <td>
                  {e.estado_revision === 'confirmado'
                    ? <span className="etiqueta-estado et-confirmado">Confirmado</span>
                    : e.estado_revision === 'pendiente'
                      ? <span className="etiqueta-estado et-pendiente">Pendiente</span>
                      : <span className="etiqueta-estado et-sin">Sin revisar</span>}
                </td>
                <td><small>{e.version_modelo}</small></td>
                <td><Link to={`/evaluaciones/${e.id}`}>Ver detalle</Link></td>
              </tr>
            ))}
            {datos && !datos.items.length && (
              <tr><td colSpan="8">No hay evaluaciones que coincidan con los filtros. Ejecuta una evaluación para este periodo o ajusta los filtros.</td></tr>
            )}
          </tbody>
        </table>
        <div className="paginacion">
          <button className="secundario" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>← Anterior</button>
          Página {pagina} de {paginas} · {datos?.total} registros
          <button className="secundario" disabled={pagina >= paginas} onClick={() => setPagina(pagina + 1)}>Siguiente →</button>
        </div>
      </div>
    </div>
  )
}
