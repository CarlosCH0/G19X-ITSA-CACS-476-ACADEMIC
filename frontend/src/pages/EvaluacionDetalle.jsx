import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { formatearFechaHora } from '../utils/fecha.js'

const CLAS = {
  alto_potencial: ['et-hipo', 'Alto potencial'],
  en_desarrollo: ['et-desarrollo', 'En desarrollo'],
  estandar: ['et-estandar', 'Estándar'],
  no_evaluable: ['et-noevaluable', 'No evaluable'],
}

export default function EvaluacionDetalle() {
  const { id } = useParams()
  const { puede } = useAuth()
  const [ev, setEv] = useState(null)
  const [error, setError] = useState('')
  const [comentario, setComentario] = useState('')
  const [textoObs, setTextoObs] = useState('')

  const cargar = () => {
    api.get(`/api/evaluaciones/${id}`).then(setEv).catch((e) => setError(e.message))
  }
  useEffect(cargar, [id])

  const revisar = async (estado) => {
    try {
      await api.post(`/api/revisiones/resultados/${ev.resultado.id}`, { estado, comentario })
      setComentario('')
      cargar()
    } catch (e) { setError(e.message) }
  }

  const regenerarExplicacion = async () => {
    try {
      const r = await api.post(`/api/evaluaciones/${id}/explicacion`)
      setEv({ ...ev, resultado: { ...ev.resultado, explicacion: r.explicacion, explicacion_origen: r.explicacion_origen } })
    } catch (e) { setError(e.message) }
  }

  const agregarObservacion = async () => {
    if (!textoObs.trim()) return
    try {
      await api.post(`/api/evaluaciones/${id}/observaciones`, { texto: textoObs })
      setTextoObs('')
      cargar()
    } catch (e) { setError(e.message) }
  }

  if (error && !ev) return <div className="error">{error}</div>
  if (!ev) return <p className="subtitulo">Cargando evaluación…</p>

  const res = ev.resultado
  const factores = res?.factores || []
  const maxContrib = Math.max(...factores.map((f) => f.contribucion), 0.0001)

  return (
    <div>
      <h1 className="titulo">Evaluación #{ev.id}</h1>
      <p className="subtitulo">
        <Link to={`/colaboradores/${ev.colaborador_id}`}>{ev.colaborador_nombre}</Link> · {ev.area} ·
        Periodo {ev.periodo} · Evaluado el {formatearFechaHora(ev.fecha)} ·
        Criterios v{ev.configuracion_version} · Modelo de cálculo {ev.version_modelo}
      </p>
      {error && <div className="error">{error}</div>}

      <div className="tarjetas">
        <div className="tarjeta">
          <div className="etiqueta">Puntuación global (0 a 100)</div>
          <div className="valor">{res?.puntuacion ?? '—'}</div>
        </div>
        <div className="tarjeta">
          <div className="etiqueta">Clasificación</div>
          <div style={{ marginTop: 6 }}>
            <span className={`etiqueta-estado ${CLAS[ev.clasificacion]?.[0] || 'et-sin'}`} style={{ fontSize: 14 }}>
              {CLAS[ev.clasificacion]?.[1] || '—'}
            </span>
          </div>
        </div>
        <div className="tarjeta" title="Porcentaje de indicadores que tienen un dato válido">
          <div className="etiqueta">Cobertura de datos</div>
          <div className="valor">{res ? Math.round(res.cobertura * 100) : 0}%</div>
        </div>
        <div className="tarjeta">
          <div className="etiqueta">Revisión humana</div>
          <div style={{ marginTop: 6, fontSize: 13 }}>
            {ev.estado_revision === 'confirmado'
              ? <span className="etiqueta-estado et-confirmado">Confirmado</span>
              : ev.estado_revision === 'pendiente'
                ? <span className="etiqueta-estado et-pendiente">Pendiente</span>
                : <span className="etiqueta-estado et-sin">Sin revisar</span>}
          </div>
        </div>
      </div>

      {ev.estado === 'incompleta' && (
        <div className="aviso">
          <b>Evaluación incompleta:</b> al colaborador le faltan datos válidos (la cobertura quedó por
          debajo del mínimo configurado). Úsala solo como referencia; lo ideal es completar las
          mediciones y volver a evaluar.
        </div>
      )}

      <div className="grid-2">
        <div className="panel">
          <h2>Cómo se calculó la puntuación</h2>
          <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>
            Cada barra indica cuánto aportó ese indicador a la puntuación final.
          </p>
          {factores.map((f) => (
            <div className="factor" key={f.codigo}>
              <div className="factor-cab">
                <span>{f.nombre} <small>({f.tipo})</small></span>
                <b>{f.contribucion.toFixed(3)} pts</b>
              </div>
              <div className="barra"><div style={{ width: `${(f.contribucion / maxContrib) * 100}%` }} /></div>
              <small style={{ color: 'var(--gris-500)' }}>
                valor registrado {f.valor} · en escala 0-100: {f.normalizado} · peso {f.peso}
              </small>
            </div>
          ))}
          {!factores.length && <p className="subtitulo">Todavía no hay factores que mostrar para esta evaluación.</p>}
        </div>

        <div>
          <div className="panel">
            <h2>Explicación del resultado (asistida por IA)</h2>
            {res?.explicacion ? (
              <>
                <p style={{ whiteSpace: 'pre-wrap' }}>{res.explicacion}</p>
                <small style={{ color: 'var(--gris-500)' }}>
                  Generada por: <b>{res.explicacion_origen === 'local_determinista' ? 'resumen automático local' : 'Azure OpenAI'}</b>
                  {res.fecha_explicacion && ` · ${formatearFechaHora(res.fecha_explicacion)}`}
                </small>
              </>
            ) : (
              <p className="subtitulo">Todavía no se ha generado una explicación para este resultado.</p>
            )}
            {puede('ia.usar') && (
              <button style={{ marginTop: 10 }} className="secundario" onClick={regenerarExplicacion}>
                🔄 Regenerar explicación
              </button>
            )}
          </div>

          {puede('evaluaciones.revisar') && res && (
            <div className="panel">
              <h2>Revisión humana obligatoria</h2>
              <p className="subtitulo" style={{ margin: '-4px 0 10px' }}>
                Confirma el resultado si los datos y la clasificación son correctos, o márcalo como
                pendiente si requiere más análisis.
              </p>
              <textarea
                style={{ width: '100%', minHeight: 70 }}
                placeholder="Comentario de la revisión (opcional)…"
                value={comentario}
                onChange={(e) => setComentario(e.target.value)}
              />
              <div className="botones" style={{ marginTop: 10 }}>
                <button className="exitoso" onClick={() => revisar('confirmado')}>✔ Confirmar resultado</button>
                <button className="secundario" onClick={() => revisar('pendiente')}>⏳ Marcar pendiente</button>
              </div>
              {res.revisiones?.length > 0 && (
                <div style={{ marginTop: 14 }}>
                  <h2>Historial de revisiones</h2>
                  {res.revisiones.map((r) => (
                    <div key={r.id} style={{ borderBottom: '1px solid var(--gris-100)', padding: '6px 0', fontSize: 13 }}>
                      <span className={`etiqueta-estado ${r.estado === 'confirmado' ? 'et-confirmado' : 'et-pendiente'}`}>
                        {r.estado === 'confirmado' ? 'Confirmado' : 'Pendiente'}
                      </span>{' '}
                      {r.usuario_nombre} · {formatearFechaHora(r.fecha)}
                      {r.comentario && <div style={{ color: 'var(--gris-700)' }}>“{r.comentario}”</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="panel">
            <h2>Observaciones</h2>
            <p className="subtitulo" style={{ margin: '-4px 0 10px' }}>Notas libres para dar contexto a esta evaluación.</p>
            {ev.observaciones.map((o) => (
              <div key={o.id} style={{ borderBottom: '1px solid var(--gris-100)', padding: '6px 0' }}>
                <div style={{ fontSize: 12, color: 'var(--gris-500)' }}>
                  {o.autor_nombre} · {formatearFechaHora(o.fecha)}
                </div>
                <div>{o.texto}</div>
              </div>
            ))}
            {!ev.observaciones.length && <p className="subtitulo">Sin observaciones.</p>}
            {puede('evaluaciones.revisar') && (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <input style={{ flex: 1 }} placeholder="Nueva observación…"
                       value={textoObs} onChange={(e) => setTextoObs(e.target.value)} />
                <button onClick={agregarObservacion}>Agregar</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
