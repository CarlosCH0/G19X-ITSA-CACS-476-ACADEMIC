import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

const VALIDEZ = {
  valida: ['et-valida', 'Válida'],
  pendiente: ['et-pendiente', 'Pendiente'],
  invalida: ['et-invalida', 'Inválida'],
}
const CLAS = {
  alto_potencial: ['et-hipo', 'Alto potencial'],
  en_desarrollo: ['et-desarrollo', 'En desarrollo'],
  estandar: ['et-estandar', 'Estándar'],
  no_evaluable: ['et-noevaluable', 'No evaluable'],
}

export default function ColaboradorDetalle() {
  const { id } = useParams()
  const { puede } = useAuth()
  const [perfil, setPerfil] = useState(null)
  const [indicadores, setIndicadores] = useState([])
  const [error, setError] = useState('')
  const [textoObs, setTextoObs] = useState('')
  const [carga, setCarga] = useState({ periodo: '', filas: {} })

  const cargar = () => {
    api.get(`/api/colaboradores/${id}/perfil`)
      .then((p) => { setPerfil(p); setCarga({ periodo: carga.periodo, filas: {} }) })
      .catch((e) => setError(e.message))
  }
  useEffect(cargar, [id])
  useEffect(() => { api.get('/api/indicadores', { solo_activos: true }).then(setIndicadores) }, [])

  const cambiarValidez = async (medicionId, validez) => {
    try {
      await api.patch(`/api/indicadores/mediciones/${medicionId}/validez`, { validez })
      cargar()
    } catch (e) { setError(e.message) }
  }

  const guardarObservacion = async () => {
    if (!textoObs.trim()) return
    try {
      await api.post(`/api/colaboradores/${id}/observaciones`, { texto: textoObs })
      setTextoObs('')
      cargar()
    } catch (e) { setError(e.message) }
  }

  const guardarMediciones = async () => {
    const mediciones = Object.entries(carga.filas)
      .filter(([, v]) => v !== '' && v !== undefined)
      .map(([indicador_id, valor]) => ({ indicador_id: Number(indicador_id), valor: Number(valor), validez: 'valida' }))
    if (!mediciones.length || !carga.periodo) { setError('Indica el periodo y al menos un valor.'); return }
    try {
      await api.post('/api/indicadores/mediciones', { colaborador_id: Number(id), periodo: carga.periodo, mediciones })
      setError('')
      cargar()
    } catch (e) { setError(e.message) }
  }

  if (error && !perfil) return <div className="error">{error}</div>
  if (!perfil) return <p className="subtitulo">Cargando perfil…</p>

  const c = perfil.colaborador
  const periodos = [...new Set(perfil.mediciones.map((m) => m.periodo))]

  return (
    <div>
      <h1 className="titulo">{c.nombre}</h1>
      <p className="subtitulo">
        {c.codigo} · {c.area} · {c.puesto} · Ingreso: {c.fecha_ingreso || '—'}{' '}
        <span className={`etiqueta-estado ${c.estado ? 'et-valida' : 'et-noevaluable'}`}>
          {c.estado ? 'Activo' : 'Inactivo'}
        </span>
      </p>
      {error && <div className="error">{error}</div>}

      <div className="grid-2">
        <div className="panel">
          <h2>Mediciones por periodo</h2>
          <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>
            Valores registrados de cada indicador. Solo las mediciones marcadas como válidas se usan para evaluar.
          </p>
          {periodos.length === 0 && <p className="subtitulo">Todavía no hay mediciones registradas para este colaborador.</p>}
          {periodos.map((p) => (
            <table className="tabla" key={p} style={{ marginBottom: 16 }}>
              <thead>
                <tr><th colSpan="4" style={{ fontSize: 13 }}>Periodo {p}</th></tr>
                <tr><th>Indicador</th><th>Valor</th><th>Validez</th><th>Acción</th></tr>
              </thead>
              <tbody>
                {perfil.mediciones.filter((m) => m.periodo === p).map((m) => (
                  <tr key={m.id}>
                    <td>{m.indicador_nombre}</td>
                    <td><b>{m.valor}</b></td>
                    <td><span className={`etiqueta-estado ${VALIDEZ[m.validez]?.[0]}`}>{VALIDEZ[m.validez]?.[1]}</span></td>
                    <td>
                      {puede('indicadores.gestionar') && m.validez !== 'valida' && (
                        <button className="secundario" onClick={() => cambiarValidez(m.id, 'valida')} title="Marcar esta medición como válida para que cuente en la evaluación">Marcar válida</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ))}

          {puede('indicadores.gestionar') && (
            <div style={{ borderTop: '1px solid var(--gris-100)', paddingTop: 14 }}>
              <h2>Registrar mediciones</h2>
              <p className="subtitulo" style={{ margin: '-4px 0 10px' }}>
                Escribe el periodo y los valores; deja en blanco lo que no quieras registrar.
              </p>
              <div className="filtros">
                <input placeholder="Periodo (ej. 2026-S2)" value={carga.periodo}
                       onChange={(e) => setCarga({ ...carga, periodo: e.target.value })} />
              </div>
              {indicadores.map((i) => (
                <div key={i.id} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'center' }}>
                  <span style={{ flex: 1, fontSize: 13 }}>{i.nombre}</span>
                  <input style={{ width: 110 }} type="number" step="0.01" placeholder="Valor"
                         value={carga.filas[i.id] ?? ''}
                         onChange={(e) => setCarga({ ...carga, filas: { ...carga.filas, [i.id]: e.target.value } })} />
                </div>
              ))}
              <button style={{ marginTop: 8 }} onClick={guardarMediciones}>Guardar mediciones</button>
            </div>
          )}
        </div>

        <div>
          <div className="panel">
            <h2>Historial de evaluaciones</h2>
            <table className="tabla">
              <thead><tr><th>Periodo</th><th>Puntuación</th><th>Clasificación</th><th>Detalle</th></tr></thead>
              <tbody>
                {perfil.historial.map((h) => (
                  <tr key={h.evaluacion_id}>
                    <td>{h.periodo}</td>
                    <td><b>{h.puntuacion ?? '—'}</b></td>
                    <td><span className={`etiqueta-estado ${CLAS[h.clasificacion]?.[0] || 'et-sin'}`}>{CLAS[h.clasificacion]?.[1] || h.estado}</span></td>
                    <td><Link to={`/evaluaciones/${h.evaluacion_id}`}>Ver</Link></td>
                  </tr>
                ))}
                {!perfil.historial.length && <tr><td colSpan="4">Sin evaluaciones todavía.</td></tr>}
              </tbody>
            </table>
          </div>

          <div className="panel">
            <h2>Observaciones</h2>
            {perfil.observaciones.map((o) => (
              <div key={o.id} style={{ borderBottom: '1px solid var(--gris-100)', padding: '8px 0' }}>
                <div style={{ fontSize: 12, color: 'var(--gris-500)' }}>
                  {o.autor_nombre} · {new Date(o.fecha).toLocaleString('es-MX')}
                </div>
                <div>{o.texto}</div>
              </div>
            ))}
            {!perfil.observaciones.length && <p className="subtitulo">Sin observaciones.</p>}
            {puede('evaluaciones.revisar') && (
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <input style={{ flex: 1 }} placeholder="Nueva observación…"
                       value={textoObs} onChange={(e) => setTextoObs(e.target.value)} />
                <button onClick={guardarObservacion}>Agregar</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

