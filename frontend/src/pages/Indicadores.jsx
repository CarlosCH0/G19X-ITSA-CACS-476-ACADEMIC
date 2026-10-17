import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

const TIPOS = {
  desempeno: 'Desempeño',
  competencia: 'Competencia',
  capacitacion: 'Capacitación',
  experiencia: 'Experiencia',
  objetivo: 'Objetivo',
  organizacional: 'Organizacional',
}

export default function Indicadores() {
  const { puede } = useAuth()
  const [lista, setLista] = useState([])
  const [error, setError] = useState('')
  const [form, setForm] = useState(null)

  const cargar = () => api.get('/api/indicadores').then(setLista).catch((e) => setError(e.message))
  useEffect(() => {
    cargar()
  }, [])

  const guardar = async () => {
    try {
      if (form.id) await api.put(`/api/indicadores/${form.id}`, form)
      else await api.post('/api/indicadores', form)
      setForm(null)
      cargar()
    } catch (e) { setError(e.message) }
  }

  return (
    <div>
      <h1 className="titulo">Indicadores de talento</h1>
      <p className="subtitulo">
        Los indicadores son los aspectos que se miden de cada colaborador (desempeño, competencias,
        capacitación, experiencia…). La columna «Cómo se interpreta» indica si un valor más alto o
        más bajo es mejor.
      </p>
      {error && <div className="error">{error}</div>}

      {puede('indicadores.gestionar') && (
        <div className="filtros">
          <button onClick={() => setForm({ codigo: '', nombre: '', tipo: 'desempeno', direccion: 'mayor_mejor' })}>
            + Nuevo indicador
          </button>
        </div>
      )}

      {form && (
        <div className="panel">
          <h2>{form.id ? 'Editar indicador' : 'Nuevo indicador'}</h2>
          <p className="subtitulo" style={{ margin: '-4px 0 10px' }}>
            El código es el identificador único del indicador y también se usa en la carga masiva CSV.
          </p>
          <div className="filtros">
            {!form.id && (
              <input placeholder="Código (ej. INNOVACION)" value={form.codigo}
                     onChange={(e) => setForm({ ...form, codigo: e.target.value.toUpperCase() })} />
            )}
            <input placeholder="Nombre" value={form.nombre}
                   onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
            <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
              {Object.entries(TIPOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <select value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} title="Define si un valor alto o bajo es positivo">
              <option value="mayor_mejor">Mientras más alto, mejor</option>
              <option value="menor_mejor">Mientras más bajo, mejor</option>
            </select>
            <button onClick={guardar}>Guardar</button>
            <button className="secundario" onClick={() => setForm(null)}>Cancelar</button>
          </div>
        </div>
      )}

      <div className="panel">
        <table className="tabla">
          <thead><tr><th>Código</th><th>Nombre</th><th>Tipo</th><th>Cómo se interpreta</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            {lista.map((i) => (
              <tr key={i.id} style={{ opacity: i.activo ? 1 : 0.55 }}>
                <td><b>{i.codigo}</b></td>
                <td>{i.nombre}</td>
                <td>{TIPOS[i.tipo]}</td>
                <td title={i.direccion === 'mayor_mejor' ? 'Un valor alto es positivo' : 'Un valor bajo es positivo'}>
                  {i.direccion === 'mayor_mejor' ? '↑ Más alto es mejor' : '↓ Más bajo es mejor'}
                </td>
                <td>
                  <span className={`etiqueta-estado ${i.activo ? 'et-valida' : 'et-noevaluable'}`}>
                    {i.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td>
                  {puede('indicadores.gestionar') && (
                    <button className="secundario" onClick={() => setForm(i)}>Editar</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
