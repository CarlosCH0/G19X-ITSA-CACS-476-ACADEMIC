import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import { formatearFecha } from '../utils/fecha.js'

export default function Configuracion() {
  const [lista, setLista] = useState([])
  const [indicadores, setIndicadores] = useState([])
  const [configuracionAreas, setConfiguracionAreas] = useState(null)
  const [areaSeleccionada, setAreaSeleccionada] = useState('')
  const [indicadoresArea, setIndicadoresArea] = useState([])
  const [guardandoArea, setGuardandoArea] = useState(false)
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')
  const [form, setForm] = useState(null) // {nombre, umbral, cobertura, pesos:{}}

  const cargar = () => {
    api.get('/api/configuracion').then(setLista).catch((e) => setError(e.message))
  }
  useEffect(() => {
    cargar()
    api.get('/api/indicadores', { solo_activos: true })
      .then(setIndicadores)
      .catch((e) => setError(e.message))
    api.get('/api/configuracion/areas-pruebas')
      .then((datos) => {
        setConfiguracionAreas(datos)
        setAreaSeleccionada((actual) =>
          datos.areas.some((item) => item.area === actual) ? actual : datos.areas[0]?.area || '')
      })
      .catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    const area = configuracionAreas?.areas.find((item) => item.area === areaSeleccionada)
    setIndicadoresArea(area?.indicador_ids || [])
  }, [configuracionAreas, areaSeleccionada])

  const nuevaVersion = () => {
    const activa = lista.find((c) => c.activa)
    const pesos = {}
    Object.entries(activa?.criterios?.pesos || {}).forEach(([k, v]) => { pesos[k] = v })
    setForm({
      nombre: '',
      umbral: activa?.umbral_hipo ?? 75,
      cobertura: activa?.reglas?.cobertura_minima ?? 0.8,
      pesos,
    })
  }

  const guardar = async () => {
    try {
      await api.post('/api/configuracion', {
        nombre: form.nombre,
        umbral_hipo: Number(form.umbral),
        cobertura_minima: Number(form.cobertura),
        pesos: form.pesos,
        activar: true,
      })
      setForm(null)
      setAviso('Nueva versión creada y activada. Las próximas evaluaciones usarán estos criterios.')
      cargar()
    } catch (e) { setError(e.message) }
  }

  const activar = async (id) => {
    try {
      await api.post(`/api/configuracion/${id}/activar`)
      cargar()
    } catch (e) { setError(e.message) }
  }

  const cambiarIndicadorArea = (id) => {
    setIndicadoresArea((actuales) => (
      actuales.includes(id)
        ? actuales.filter((indicadorId) => indicadorId !== id)
        : [...actuales, id]
    ))
  }

  const guardarPruebasArea = async () => {
    try {
      setGuardandoArea(true)
      const actualizado = await api.put('/api/configuracion/areas-pruebas', {
        area: areaSeleccionada,
        indicador_ids: indicadoresArea,
      })
      setConfiguracionAreas(actualizado)
      setAviso(`Pruebas de ${areaSeleccionada} actualizadas. Los resultados históricos se conservan.`)
    } catch (e) {
      setError(e.message)
    } finally {
      setGuardandoArea(false)
    }
  }

  const suma = form ? Object.values(form.pesos).reduce((a, b) => a + Number(b || 0), 0) : 0

  return (
    <div>
      <h1 className="titulo">Configuración de criterios</h1>
      <p className="subtitulo">
        Define cómo se evalúa: cuánto aporta cada indicador a la puntuación (pesos), la puntuación
        mínima para ser alto potencial (umbral) y los datos válidos mínimos que debe tener cada
        colaborador (cobertura). Solo una versión puede estar activa; las anteriores se conservan.
      </p>
      {error && <div className="error">{error}</div>}
      {aviso && <div className="aviso">{aviso}</div>}

      <div className="panel">
        <h2>Pruebas por área</h2>
        <p className="subtitulo" style={{ margin: '-4px 0 12px' }}>
          Cada área se evalúa solo con los indicadores asignados aquí. Las áreas actuales se
          inicializaron con todas las pruebas vigentes; agregar una prueba no elimina indicadores
          del catálogo ni cambia evaluaciones anteriores.
        </p>
        {configuracionAreas?.areas.length ? (
          <>
            <label style={{ display: 'inline-grid', gap: 4, marginBottom: 12 }}>
              Área
              <select value={areaSeleccionada} onChange={(e) => setAreaSeleccionada(e.target.value)}>
                {configuracionAreas.areas.map((area) => (
                  <option key={area.area} value={area.area}>{area.area}</option>
                ))}
              </select>
            </label>
            <div style={{ display: 'grid', gap: 8, marginBottom: 14 }}>
              {configuracionAreas.indicadores.map((indicador) => {
                const seleccionado = indicadoresArea.includes(indicador.id)
                const disponible = indicador.activo && indicador.en_criterios
                return (
                  <label key={indicador.id} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <input
                      type="checkbox"
                      checked={seleccionado}
                      disabled={guardandoArea || (!seleccionado && !disponible)}
                      onChange={() => cambiarIndicadorArea(indicador.id)}
                    />
                    <span>
                      {indicador.nombre} <small>({indicador.codigo})</small>
                      {!indicador.activo && <small> — indicador inactivo</small>}
                      {indicador.activo && !indicador.en_criterios && <small> — sin peso en la versión activa</small>}
                    </span>
                  </label>
                )
              })}
            </div>
            <p className="subtitulo">
              Seleccionadas: <b>{indicadoresArea.length}</b>. Para agregar una prueba, debe ser un
              indicador activo con peso en la versión vigente.
            </p>
            <button onClick={guardarPruebasArea} disabled={guardandoArea || !areaSeleccionada}>
              {guardandoArea ? 'Guardando…' : 'Guardar pruebas del área'}
            </button>
          </>
        ) : configuracionAreas ? (
          <p className="subtitulo">No hay áreas con colaboradores activos para configurar.</p>
        ) : (
          <p className="subtitulo">Cargando áreas y pruebas…</p>
        )}
      </div>

      <div className="filtros">
        <button onClick={nuevaVersion} title="Crea una copia de la versión activa para modificarla">+ Nueva versión (copia de la activa)</button>
      </div>

      {form && (
        <div className="panel">
          <h2>Nueva versión de criterios</h2>
          <p className="subtitulo" style={{ margin: '-4px 0 10px' }}>
            Al crear y activar la versión, las próximas evaluaciones usarán estos valores.
          </p>
          <div className="filtros">
            <input placeholder="Nombre de la versión" value={form.nombre}
                   onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
            <label title="Puntuación (0 a 100) a partir de la cual un colaborador se clasifica como alto potencial">Umbral alto potencial: <input type="number" style={{ width: 80 }} value={form.umbral}
                   onChange={(e) => setForm({ ...form, umbral: e.target.value })} /></label>
            <label title="Porción mínima de indicadores con dato válido (0 a 1) para que la evaluación sea completa">Cobertura mínima: <input type="number" step="0.05" style={{ width: 70 }} value={form.cobertura}
                   onChange={(e) => setForm({ ...form, cobertura: e.target.value })} /></label>
          </div>
          <table className="tabla">
            <thead><tr><th>Indicador</th><th>Peso</th></tr></thead>
            <tbody>
              {indicadores.map((i) => (
                <tr key={i.id}>
                  <td>{i.nombre} <small>({i.codigo})</small></td>
                  <td>
                    <input type="number" step="0.01" style={{ width: 90 }}
                           value={form.pesos[i.codigo] ?? ''}
                           onChange={(e) => setForm({ ...form, pesos: { ...form.pesos, [i.codigo]: e.target.value } })} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="subtitulo">Los pesos definen cuánto aporta cada indicador a la puntuación final. Suma actual: <b>{suma.toFixed(2)}</b> (se recomienda 1.00)</p>
          <div className="botones">
            <button onClick={guardar}>Crear y activar</button>
            <button className="secundario" onClick={() => setForm(null)}>Cancelar</button>
          </div>
        </div>
      )}

      <div className="panel">
        <table className="tabla">
          <thead><tr><th>Versión</th><th>Nombre</th><th>Umbral alto potencial</th><th>Cobertura mín.</th><th>Pesos</th><th>Estado</th><th>Creada</th><th></th></tr></thead>
          <tbody>
            {lista.map((c) => (
              <tr key={c.id}>
                <td><b>v{c.version}</b></td>
                <td>{c.nombre}</td>
                <td>{c.umbral_hipo}</td>
                <td>{c.reglas?.cobertura_minima ?? '—'}</td>
                <td><small>{Object.entries(c.criterios?.pesos || {}).map(([k, v]) => `${k}:${v}`).join(' · ')}</small></td>
                <td>
                  <span className={`etiqueta-estado ${c.activa ? 'et-valida' : 'et-sin'}`} title={c.activa ? 'Esta versión se usa en las nuevas evaluaciones' : 'Versión anterior; se conserva como historial'}>
                    {c.activa ? 'Activa' : 'Inactiva'}
                  </span>
                </td>
                <td>{formatearFecha(c.fecha_creacion)}</td>
                <td>
                  {!c.activa && (
                    <button className="secundario" onClick={() => activar(c.id)}>Activar</button>
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
