import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { formatearFechaHora } from '../utils/fecha.js'

export default function Auditoria() {
  const [datos, setDatos] = useState(null)
  const [q, setQ] = useState('')
  const [accion, setAccion] = useState('')
  const [pagina, setPagina] = useState(1)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/auditoria', { q, accion, pagina, tamanio: 25 })
      .then(setDatos).catch((e) => setError(e.message))
  }, [q, accion, pagina])

  const paginas = datos ? Math.max(1, Math.ceil(datos.total / datos.tamanio)) : 1

  return (
    <div>
      <h1 className="titulo">Registro de auditoría</h1>
      <p className="subtitulo">
        Historial de quién hizo qué y cuándo: inicios de sesión, altas y cambios de datos,
        ejecución de evaluaciones y cambios de criterios.
      </p>
      {error && <div className="error">{error}</div>}

      <div className="filtros">
        <input placeholder="Buscar por usuario, recurso o acción…" value={q}
               onChange={(e) => { setPagina(1); setQ(e.target.value) }} />
        <input placeholder="Filtrar por acción exacta (ej. evaluacion.ejecutar)" value={accion}
               onChange={(e) => { setPagina(1); setAccion(e.target.value) }} />
      </div>

      <div className="panel">
        <table className="tabla">
          <thead><tr><th>Fecha/Hora</th><th>Usuario</th><th>Acción</th><th>Recurso</th><th>Detalle</th></tr></thead>
          <tbody>
            {datos?.items.map((a) => (
              <tr key={a.id}>
                <td style={{ whiteSpace: 'nowrap' }}>{formatearFechaHora(a.fecha_hora)}</td>
                <td>{a.usuario_nombre}</td>
                <td><b>{a.accion}</b></td>
                <td>{a.recurso}</td>
                <td><small>{a.detalle ? JSON.stringify(a.detalle) : '—'}</small></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="paginacion">
          <button className="secundario" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>← Anterior</button>
          Página {pagina} de {paginas} · {datos?.total} eventos
          <button className="secundario" disabled={pagina >= paginas} onClick={() => setPagina(pagina + 1)}>Siguiente →</button>
        </div>
      </div>
    </div>
  )
}
