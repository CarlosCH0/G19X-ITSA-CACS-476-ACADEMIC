import { useEffect, useState } from 'react'
import { api } from '../api/client.js'

export default function Usuarios() {
  const [datos, setDatos] = useState(null)
  const [roles, setRoles] = useState([])
  const [error, setError] = useState('')
  const [form, setForm] = useState(null)

  const cargar = () => {
    api.get('/api/usuarios', { tamanio: 100 }).then(setDatos).catch((e) => setError(e.message))
  }
  useEffect(() => {
    cargar()
    api.get('/api/usuarios/roles').then(setRoles)
  }, [])

  const guardar = async () => {
    try {
      if (form.id) {
        const cuerpo = { nombre: form.nombre, rol_id: Number(form.rol_id), estado: form.estado !== false }
        if (form.password) cuerpo.password = form.password
        await api.put(`/api/usuarios/${form.id}`, cuerpo)
      } else {
        await api.post('/api/usuarios', {
          nombre: form.nombre, correo: form.correo,
          password: form.password, rol_id: Number(form.rol_id),
        })
      }
      setForm(null)
      cargar()
    } catch (e) { setError(e.message) }
  }

  const rolNombre = (id) => roles.find((r) => r.id === id)?.nombre || id

  return (
    <div>
      <h1 className="titulo">Usuarios y roles</h1>
      <p className="subtitulo">
        Gestiona quién puede entrar al sistema y qué puede hacer. Cada usuario tiene un rol que
        determina sus permisos: Administrador, Gestor de Talento, Evaluador o Consulta.
      </p>
      {error && <div className="error">{error}</div>}

      <div className="filtros">
        <button onClick={() => setForm({ nombre: '', correo: '', password: '', rol_id: roles[0]?.id })}>
          + Nuevo usuario
        </button>
      </div>

      {form && (
        <div className="panel">
          <h2>{form.id ? `Editar: ${form.nombre}` : 'Nuevo usuario'}</h2>
          <div className="filtros">
            <input placeholder="Nombre completo" value={form.nombre}
                   onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
            {!form.id && (
              <input placeholder="correo@develop.com.mx" type="email" value={form.correo}
                     onChange={(e) => setForm({ ...form, correo: e.target.value })} />
            )}
            <input placeholder={form.id ? 'Nueva contraseña (opcional)' : 'Contraseña (mín. 8)'} type="password"
                   value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            <select value={form.rol_id} onChange={(e) => setForm({ ...form, rol_id: e.target.value })}>
              {roles.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
            </select>
            <button onClick={guardar}>Guardar</button>
            <button className="secundario" onClick={() => setForm(null)}>Cancelar</button>
          </div>
        </div>
      )}

      <div className="panel">
        <table className="tabla">
          <thead><tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            {datos?.items.map((u) => (
              <tr key={u.id} style={{ opacity: u.estado ? 1 : 0.55 }}>
                <td>{u.nombre}</td>
                <td>{u.correo}</td>
                <td><span className="etiqueta-estado et-sin">{rolNombre(u.rol_id)}</span></td>
                <td>
                  <span className={`etiqueta-estado ${u.estado ? 'et-valida' : 'et-noevaluable'}`}>
                    {u.estado ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td>
                  <button className="secundario" onClick={() => setForm({ ...u, password: '' })}>Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h2>Matriz de permisos por rol</h2>
        <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>
          Los permisos se leen «módulo.acción»; por ejemplo, <b>reportes.consultar</b> permite ver los reportes.
        </p>
        <table className="tabla">
          <thead><tr><th>Rol</th><th>Permisos</th></tr></thead>
          <tbody>
            {roles.map((r) => (
              <tr key={r.id}>
                <td><b>{r.nombre}</b></td>
                <td>{r.permisos.map((p) => (
                  <span key={p.codigo} className="etiqueta-estado et-sin" style={{ margin: 2, display: 'inline-block' }}>
                    {p.codigo}
                  </span>
                ))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
