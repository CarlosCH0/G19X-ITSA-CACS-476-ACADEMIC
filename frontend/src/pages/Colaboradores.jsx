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

function ModalColaborador({ inicial, onGuardar, onCerrar }) {
  const [form, setForm] = useState(inicial || { codigo: '', nombre: '', area: '', puesto: '', fecha_ingreso: '' })
  return (
    <div className="panel">
      <h2>{inicial ? 'Editar colaborador' : 'Nuevo colaborador'}</h2>
      <form
        onSubmit={(e) => { e.preventDefault(); onGuardar(form) }}
        style={{ display: 'grid', gap: 10, maxWidth: 420 }}
      >
        {!inicial && (
          <input placeholder="Código (ej. COL-050)" value={form.codigo} required
                 onChange={(e) => setForm({ ...form, codigo: e.target.value })} />
        )}
        <input placeholder="Nombre completo" value={form.nombre} required
               onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
        <input placeholder="Área o departamento (ej. Tecnología)" value={form.area} required
               onChange={(e) => setForm({ ...form, area: e.target.value })} />
        <input placeholder="Puesto (opcional)" value={form.puesto}
               onChange={(e) => setForm({ ...form, puesto: e.target.value })} />
        <label style={{ fontSize: 12.5, color: 'var(--gris-700)', display: 'grid', gap: 4 }}>
          Fecha de ingreso (opcional)
          <input type="date" value={form.fecha_ingreso || ''}
                 onChange={(e) => setForm({ ...form, fecha_ingreso: e.target.value })} />
        </label>
        <div className="botones">
          <button type="submit">Guardar</button>
          <button type="button" className="secundario" onClick={onCerrar}>Cancelar</button>
        </div>
      </form>
    </div>
  )
}

export default function Colaboradores() {
  const { puede } = useAuth()
  const [datos, setDatos] = useState(null)
  const [q, setQ] = useState('')
  const [area, setArea] = useState('')
  const [pagina, setPagina] = useState(1)
  const [error, setError] = useState('')
  const [editando, setEditando] = useState(null) // null | {} | colaborador

  const cargar = () => {
    api.get('/api/colaboradores', { q, area, pagina, tamanio: 12, incluir_inactivos: true })
      .then(setDatos).catch((e) => setError(e.message))
  }
  useEffect(cargar, [q, area, pagina])

  const guardar = async (form) => {
    try {
      if (editando?.id) await api.put(`/api/colaboradores/${editando.id}`, form)
      else await api.post('/api/colaboradores', form)
      setEditando(null)
      cargar()
    } catch (e) { setError(e.message) }
  }

  const desactivar = async (c) => {
    if (!window.confirm(`¿Desactivar a ${c.nombre}? Dejará de participar en nuevas evaluaciones, pero su historial se conserva.`)) return
    try { await api.delete(`/api/colaboradores/${c.id}`); cargar() } catch (e) { setError(e.message) }
  }

  const paginas = datos ? Math.max(1, Math.ceil(datos.total / datos.tamanio)) : 1

  return (
    <div>
      <h1 className="titulo">Colaboradores</h1>
      <p className="subtitulo">Registra, consulta, edita o desactiva colaboradores. Desactivar no borra nada: el historial se conserva completo.</p>
      {error && <div className="error">{error}</div>}

      <div className="filtros">
        <input placeholder="Buscar por nombre o código…" value={q} onChange={(e) => { setPagina(1); setQ(e.target.value) }} />
        <input placeholder="Área" value={area} onChange={(e) => { setPagina(1); setArea(e.target.value) }} />
        {puede('colaboradores.gestionar') && !editando && (
          <button onClick={() => setEditando({})}>+ Nuevo colaborador</button>
        )}
      </div>

      {editando !== null && (
        <ModalColaborador
          inicial={editando.id ? editando : null}
          onGuardar={guardar}
          onCerrar={() => setEditando(null)}
        />
      )}

      <div className="panel">
        <table className="tabla">
          <thead>
            <tr><th>Código</th><th>Nombre</th><th>Área</th><th>Puesto</th><th>Última evaluación</th><th>Estado</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            {datos?.items.map((c) => (
              <tr key={c.id} style={{ opacity: c.estado ? 1 : 0.55 }}>
                <td>{c.codigo}</td>
                <td><Link to={`/colaboradores/${c.id}`}>{c.nombre}</Link></td>
                <td>{c.area}</td>
                <td>{c.puesto}</td>
                <td>
                  {c.ultima_puntuacion != null ? (
                    <>
                      <b>{c.ultima_puntuacion}</b>{' '}
                      <span className={`etiqueta-estado ${CLAS[c.ultima_clasificacion]?.[0] || 'et-sin'}`}>
                        {CLAS[c.ultima_clasificacion]?.[1] || '—'}
                      </span>{' '}
                      <small>({c.ultimo_periodo})</small>
                    </>
                  ) : '—'}
                </td>
                <td>
                  <span className={`etiqueta-estado ${c.estado ? 'et-valida' : 'et-noevaluable'}`}>
                    {c.estado ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="botones">
                  {puede('colaboradores.gestionar') && c.estado && (
                    <>
                      <button className="secundario" onClick={() => setEditando(c)}>Editar</button>
                      <button className="peligro" onClick={() => desactivar(c)}>Desactivar</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
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
