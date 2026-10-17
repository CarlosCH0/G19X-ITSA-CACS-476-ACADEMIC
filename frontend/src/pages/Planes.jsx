import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { formatearFecha } from '../utils/fecha.js'

const ESTADOS = {
  planificado: ['et-sin', 'Planificado'],
  en_progreso: ['et-desarrollo', 'En progreso'],
  completado: ['et-confirmado', 'Completado'],
  cancelado: ['et-noevaluable', 'Cancelado'],
}
const hoy = () => new Date().toISOString().slice(0, 10)

export default function Planes() {
  const { puede } = useAuth()
  const [datos, setDatos] = useState(null)
  const [stats, setStats] = useState(null)
  const [colaboradores, setColaboradores] = useState([])
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [filtros, setFiltros] = useState({ q: '', estado: '', solo_abiertos: false, pagina: 1 })
  const [detalle, setDetalle] = useState(null)
  const [form, setForm] = useState(null)

  const cargar = () => {
    const params = { pagina: filtros.pagina }
    if (filtros.q) params.q = filtros.q
    if (filtros.estado) params.estado = filtros.estado
    if (filtros.solo_abiertos) params.solo_abiertos = true
    api.get('/api/planes', params).then(setDatos).catch((e) => setError(e.message))
    api.get('/api/planes/estadisticas').then(setStats).catch(() => {})
  }
  useEffect(cargar, [filtros])
  useEffect(() => {
    api.get('/api/colaboradores', { tamanio: 100 }).then((p) => setColaboradores(p.items)).catch(() => {})
  }, [])

  const abrirDetalle = (id) =>
    api.get(`/api/planes/${id}`).then(setDetalle).catch((e) => setError(e.message))

  const guardar = async () => {
    try {
      await api.post('/api/planes', form)
      setForm(null)
      setError('')
      setAviso('Plan creado correctamente.')
      cargar()
    } catch (e) { setError(e.message) }
  }

  const cambiarEstado = async (id, estado) => {
    try {
      await api.put(`/api/planes/${id}`, { estado })
      abrirDetalle(id)
      cargar()
    } catch (e) { setError(e.message) }
  }

  const marcarAccion = async (accionId, completada, planId) => {
    try {
      await api.patch(`/api/planes/acciones/${accionId}`, { completada })
      abrirDetalle(planId)
      cargar()
    } catch (e) { setError(e.message) }
  }

  const agregarAccion = async () => {
    if (!detalle.nuevaAccion?.trim()) return
    try {
      await api.post(`/api/planes/${detalle.id}/acciones`, { descripcion: detalle.nuevaAccion })
      abrirDetalle(detalle.id)
      cargar()
    } catch (e) { setError(e.message) }
  }

  const eliminar = async (id) => {
    if (!window.confirm('¿Eliminar el plan y sus acciones? Esta operación no se puede deshacer.')) return
    try {
      await api.delete(`/api/planes/${id}`)
      setDetalle(null)
      cargar()
    } catch (e) { setError(e.message) }
  }

  const nuevaForm = () => ({
    colaborador_id: colaboradores[0]?.id || '',
    titulo: '', objetivo: '', foco: 'liderazgo',
    fecha_inicio: hoy(), fecha_fin: hoy(),
    acciones: [{ descripcion: '', fecha_limite: '' }],
  })

  return (
    <div>
      <h1 className="titulo">Planes de desarrollo y sucesión</h1>
      <p className="subtitulo">
        Acciones para preparar talento (capacitaciones, mentorías, retos…) antes de una sucesión o un
        nuevo rol. El avance se recalcula al marcar cada acción como hecha.
      </p>
      {error && <div className="error">{error}</div>}
      {aviso && <div className="aviso">{aviso}</div>}

      {stats && (
        <div className="tarjetas">
          <div className="tarjeta"><div className="etiqueta">Planes totales</div><div className="valor">{stats.total}</div></div>
          <div className="tarjeta"><div className="etiqueta">Avance promedio</div><div className="valor">{stats.avance_promedio}%</div></div>
          <div className="tarjeta"><div className="etiqueta">En riesgo</div><div className="valor" style={{ color: 'var(--ambar)' }}>{stats.en_riesgo}</div></div>
          <div className="tarjeta"><div className="etiqueta">Vencidos sin cerrar</div><div className="valor" style={{ color: 'var(--rojo)' }}>{stats.vencidos}</div></div>
        </div>
      )}

      <div className="filtros">
        <input placeholder="Buscar por título, objetivo o colaborador" value={filtros.q}
               onChange={(e) => setFiltros({ ...filtros, q: e.target.value, pagina: 1 })} />
        <select value={filtros.estado} onChange={(e) => setFiltros({ ...filtros, estado: e.target.value, pagina: 1 })}>
          <option value="">Todos los estados</option>
          {Object.entries(ESTADOS).map(([k, v]) => <option key={k} value={k}>{v[1]}</option>)}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }} title="Oculta los planes completados y cancelados">
          <input type="checkbox" checked={filtros.solo_abiertos}
                 onChange={(e) => setFiltros({ ...filtros, solo_abiertos: e.target.checked, pagina: 1 })} />
          Solo planes abiertos
        </label>
        {puede('planes.gestionar') && (
          <button onClick={() => setForm(nuevaForm())}>+ Nuevo plan</button>
        )}
      </div>

      {form && (
        <div className="panel">
          <h2>Nuevo plan de desarrollo</h2>
          <div className="filtros">
            <select value={form.colaborador_id} onChange={(e) => setForm({ ...form, colaborador_id: Number(e.target.value) })}>
              {colaboradores.map((c) => <option key={c.id} value={c.id}>{c.codigo} — {c.nombre}</option>)}
            </select>
            <input style={{ flex: 1 }} placeholder="Título (ej. Ruta de sucesión a Tech Lead)" value={form.titulo}
                   onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
            <select value={form.foco} onChange={(e) => setForm({ ...form, foco: e.target.value })}>
              <option value="liderazgo">Liderazgo</option>
              <option value="especialista">Especialista</option>
              <option value="desarrollo">Desarrollo</option>
            </select>
          </div>
          <div className="filtros">
            <input style={{ flex: 1 }} placeholder="Objetivo del plan" value={form.objetivo}
                   onChange={(e) => setForm({ ...form, objetivo: e.target.value })} />
            <label style={{ fontSize: 12.5 }}>Inicio
              <input type="date" lang="es-MX" value={form.fecha_inicio}
                     onChange={(e) => setForm({ ...form, fecha_inicio: e.target.value })} />
            </label>
            <label style={{ fontSize: 12.5 }}>Fin
              <input type="date" lang="es-MX" value={form.fecha_fin}
                     onChange={(e) => setForm({ ...form, fecha_fin: e.target.value })} />
            </label>
          </div>
          <h2 style={{ fontSize: 13 }}>Acciones</h2>
          {form.acciones.map((a, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'center' }}>
              <input style={{ flex: 1 }} placeholder={`Acción ${i + 1}`} value={a.descripcion}
                     onChange={(e) => {
                       const acciones = [...form.acciones]
                       acciones[i] = { ...a, descripcion: e.target.value }
                       setForm({ ...form, acciones })
                     }} />
              <input style={{ width: 150 }} type="date" lang="es-MX" value={a.fecha_limite}
                     onChange={(e) => {
                       const acciones = [...form.acciones]
                       acciones[i] = { ...a, fecha_limite: e.target.value }
                       setForm({ ...form, acciones })
                     }} />
              {form.acciones.length > 1 && (
                <button className="secundario"
                        onClick={() => setForm({ ...form, acciones: form.acciones.filter((_, j) => j !== i) })}>✕</button>
              )}
            </div>
          ))}
          <div className="botones" style={{ marginTop: 10 }}>
            <button className="secundario"
                    onClick={() => setForm({ ...form, acciones: [...form.acciones, { descripcion: '', fecha_limite: '' }] })}>
              + Agregar acción
            </button>
            <button onClick={guardar} disabled={!form.titulo.trim() || !form.colaborador_id}>Guardar plan</button>
            <button className="secundario" onClick={() => setForm(null)}>Cancelar</button>
          </div>
        </div>
      )}

      <div className="panel">
        {datos === null ? (
          <p className="subtitulo">Cargando planes…</p>
        ) : (
          <>
            <table className="tabla">
              <thead>
                <tr><th>Plan</th><th>Colaborador</th><th>Foco</th><th>Fechas</th><th>Avance</th><th>Estado</th><th></th></tr>
              </thead>
              <tbody>
                {datos.items.map((p) => (
                  <tr key={p.id}>
                    <td><b>{p.titulo}</b>{p.en_riesgo && <span className="etiqueta-estado et-invalida" style={{ marginLeft: 8 }}>⚠ Riesgo</span>}</td>
                    <td><Link to={`/colaboradores/${p.colaborador_id}`}>{p.colaborador_nombre}</Link>
                      <div style={{ fontSize: 11.5, color: 'var(--gris-500)' }}>{p.area}</div></td>
                    <td style={{ textTransform: 'capitalize' }}>{p.foco}</td>
                    <td style={{ fontSize: 12.5 }}>{formatearFecha(p.fecha_inicio)} → {formatearFecha(p.fecha_fin)}</td>
                    <td style={{ minWidth: 130 }}>
                      <div className="factor-cab" style={{ fontSize: 11.5 }}>
                        <span>{p.acciones_completadas}/{p.total_acciones}</span><b>{p.progreso}%</b>
                      </div>
                      <div className="barra"><div style={{ width: `${p.progreso}%` }} /></div>
                    </td>
                    <td><span className={`etiqueta-estado ${ESTADOS[p.estado]?.[0]}`}>{ESTADOS[p.estado]?.[1]}</span></td>
                    <td><button className="secundario" onClick={() => abrirDetalle(p.id)}>Ver</button></td>
                  </tr>
                ))}
                {!datos.items.length && <tr><td colSpan="7">Sin planes que coincidan con los filtros.</td></tr>}
              </tbody>
            </table>
            {datos.total > 20 && (
              <div className="paginacion">
                Página {filtros.pagina} de {Math.ceil(datos.total / 20)} · {datos.total} planes
                <button className="secundario" disabled={filtros.pagina <= 1}
                        onClick={() => setFiltros({ ...filtros, pagina: filtros.pagina - 1 })}>← Anterior</button>
                <button className="secundario" disabled={filtros.pagina >= Math.ceil(datos.total / 20)}
                        onClick={() => setFiltros({ ...filtros, pagina: filtros.pagina + 1 })}>Siguiente →</button>
              </div>
            )}
          </>
        )}
      </div>

      {detalle && (
        <div className="modal-fondo" onClick={(e) => e.target === e.currentTarget && setDetalle(null)}>
          <div className="modal-caja">
            <div className="modal-cab">
              <h2>{detalle.titulo}</h2>
              <button className="secundario" onClick={() => setDetalle(null)}>✕</button>
            </div>
            <p className="subtitulo" style={{ marginBottom: 10 }}>
              <Link to={`/colaboradores/${detalle.colaborador_id}`}>{detalle.colaborador_nombre}</Link>
              {' '}· {detalle.area} · {detalle.puesto} · {formatearFecha(detalle.fecha_inicio)} → {formatearFecha(detalle.fecha_fin)}
            </p>
            {detalle.objetivo && <p style={{ marginTop: 0 }}>{detalle.objetivo}</p>}
            <div className="botones" style={{ margin: '10px 0' }}>
              <span className={`etiqueta-estado ${ESTADOS[detalle.estado]?.[0]}`}>{ESTADOS[detalle.estado]?.[1]}</span>
              <b>{detalle.progreso}%</b>
              <span style={{ fontSize: 12.5, color: 'var(--gris-500)' }}>
                Responsable: {detalle.responsable_nombre || 'Sin asignar'} · Creado por {detalle.creado_por_nombre}
              </span>
            </div>
            <h2 style={{ fontSize: 14 }}>Acciones del plan</h2>
            {detalle.acciones.map((a) => {
              const vencida = a.fecha_limite && !a.completada && a.fecha_limite < hoy()
              return (
                <div key={a.id} className="accion-plan">
                  <label style={{ display: 'flex', gap: 10, alignItems: 'center', flex: 1 }}>
                    {puede('planes.gestionar') ? (
                      <input type="checkbox" checked={a.completada}
                             onChange={(e) => marcarAccion(a.id, e.target.checked, detalle.id)} />
                    ) : (
                      <span>{a.completada ? '✔' : '○'}</span>
                    )}
                    <span style={{ textDecoration: a.completada ? 'line-through' : 'none', color: vencida ? 'var(--rojo)' : undefined }}>
                      {a.descripcion}
                    </span>
                  </label>
                  <span style={{ fontSize: 12, color: 'var(--gris-500)' }}>
                    {a.fecha_limite ? `Límite: ${formatearFecha(a.fecha_limite)}` : 'Sin límite'}
                    {vencida && <b style={{ color: 'var(--rojo)' }}> · vencida</b>}
                  </span>
                </div>
              )
            })}
            {!detalle.acciones.length && <p className="subtitulo">Sin acciones registradas.</p>}
            {puede('planes.gestionar') && !['completado', 'cancelado'].includes(detalle.estado) && (
              <div className="filtros" style={{ marginTop: 12 }}>
                <input style={{ flex: 1 }} placeholder="Nueva acción (capacitación, mentoría, reto…)"
                       value={detalle.nuevaAccion || ''}
                       onChange={(e) => setDetalle({ ...detalle, nuevaAccion: e.target.value })} />
                <button onClick={agregarAccion}>Agregar</button>
              </div>
            )}
            {puede('planes.gestionar') && (
              <div className="botones" style={{ marginTop: 14 }}>
                {!['completado', 'cancelado'].includes(detalle.estado) && (
                  <>
                    <button className="exitoso" onClick={() => cambiarEstado(detalle.id, 'completado')}>Marcar completado</button>
                    <button className="secundario" onClick={() => cambiarEstado(detalle.id, 'cancelado')}>Cancelar plan</button>
                  </>
                )}
                {detalle.estado === 'cancelado' && (
                  <button onClick={() => cambiarEstado(detalle.id, 'en_progreso')}>Reactivar plan</button>
                )}
                <button className="peligro" onClick={() => eliminar(detalle.id)}>Eliminar</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
