import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'

const CLAS = {
  alto_potencial: ['et-hipo', 'Alto potencial'],
  en_desarrollo: ['et-desarrollo', 'En desarrollo'],
  estandar: ['et-estandar', 'Estándar'],
  no_evaluable: ['et-noevaluable', 'No evaluable'],
}
// La fila superior representa potencial alto; las columnas van de desempeno bajo a alto.
const NIVELES = ['bajo', 'medio', 'alto']

export default function MatrizSucesion() {
  const [datos, setDatos] = useState(null)
  const [periodos, setPeriodos] = useState([])
  const [periodo, setPeriodo] = useState('')
  const [error, setError] = useState('')
  const [cajaAbierta, setCajaAbierta] = useState(null)

  useEffect(() => {
    api.get('/api/indicadores/periodos').then(setPeriodos).catch(() => {})
  }, [])
  useEffect(() => {
    api.get('/api/reportes/matriz-9box', periodo ? { periodo } : {})
      .then(setDatos).catch((e) => setError(e.message))
  }, [periodo])

  if (error) return <div className="error">{error}</div>
  if (!datos) return <p className="subtitulo">Calculando matriz de sucesión…</p>

  const obtenerCaja = (desempeno, potencial) => datos.cajas[`${desempeno}|${potencial}`] || []
  const intensidad = (n) => ({ bajo: 0, medio: 1, alto: 2 }[n])

  return (
    <div>
      <h1 className="titulo">Matriz de sucesión (9-box)</h1>
      <p className="subtitulo">
        Cada evaluado se ubica en una casilla según dos ejes: su <b>desempeño actual</b> (de menor a
        mayor hacia la derecha) y su <b>potencial futuro</b> (de menor a mayor hacia arriba). La casilla
        destacada reúne a las «estrellas» · Periodo: <b>{datos.periodo || '—'}</b>
      </p>

      <div className="filtros">
        <select value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
          <option value="">Periodo más reciente</option>
          {periodos.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <span style={{ fontSize: 13, color: 'var(--gris-700)' }}>{datos.total_evaluados} colaboradores evaluados</span>
      </div>

      {datos.total_evaluados === 0 && <div className="aviso">Sin evaluaciones para el periodo seleccionado.</div>}

      <div className="panel" style={{ overflowX: 'auto' }}>
        <div className="matriz-wrap">
          <div className="matriz-eje-y">Potencial →</div>
          <div className="matriz-grid">
            {[...NIVELES].reverse().map((potencial) =>
              NIVELES.map((desempeno) => {
                const puntos = obtenerCaja(desempeno, potencial)
                const clave = `${desempeno}|${potencial}`
                const destacada = potencial === 'alto' && desempeno === 'alto'
                return (
                  <div
                    key={clave}
                    className={`caja-n9 dest-${intensidad(potencial) * 3 + intensidad(desempeno)}${destacada ? ' destacada' : ''}`}
                    onClick={() => puntos.length && setCajaAbierta({ titulo: datos.etiquetas[clave], puntos })}
                  >
                    <div className="caja-n9-titulo">{datos.etiquetas[clave]}</div>
                    {puntos.length > 0 && (
                      <>
                        <div className="caja-n9-contador">{puntos.length}</div>
                        <div className="caja-n9-nombres">
                          {puntos.slice(0, 4).map((p) => (
                            <span key={p.evaluacion_id}>{p.nombre.split(' ').slice(0, 2).join(' ')}</span>
                          ))}
                          {puntos.length > 4 && <span style={{ color: 'var(--gris-500)' }}>+{puntos.length - 4} más…</span>}
                        </div>
                      </>
                    )}
                  </div>
                )
              })
            )}
            <div className="matriz-eje-x">Desempeño →</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h2>Cómo se dividen los ejes</h2>
          <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>
            Cada eje se divide en tres grupos de tamaño similar; la tabla muestra los puntos de corte.
          </p>
          <table className="tabla">
            <thead><tr><th>Eje</th><th>Corte entre bajo y medio</th><th>Corte entre medio y alto</th></tr></thead>
            <tbody>
              <tr><td>Desempeño</td><td>{datos.cortes.desempeno.bajo}</td><td>{datos.cortes.desempeno.alto}</td></tr>
              <tr><td>Potencial (puntuación HiPo)</td><td>{datos.cortes.potencial.bajo}</td><td>{datos.cortes.potencial.alto}</td></tr>
            </tbody>
          </table>
          <p className="subtitulo" style={{ marginTop: 10 }}>
            El desempeño se calcula con el promedio de los indicadores de tipo desempeño; el potencial es
            la puntuación global HiPo (0 a 100) del colaborador.
          </p>
        </div>
        <div className="panel">
          <h2>Lectura de la matriz</h2>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13.5, lineHeight: 1.7 }}>
            <li><b>Estrellas (alto/alto)</b>: candidaturas naturales para sucesión inmediata.</li>
            <li><b>Alto potencial emergente (medio/alto)</b>: fortalecer desempeño con retos dirigidos.</li>
            <li><b>Especialistas expertos (alto/bajo)</b>: carrera técnica o de especialización.</li>
            <li>Haz clic en cualquier caja para ver el detalle de sus colaboradores.</li>
          </ul>
        </div>
      </div>

      {cajaAbierta && (
        <div className="modal-fondo" onClick={(e) => e.target === e.currentTarget && setCajaAbierta(null)}>
          <div className="modal-caja">
            <div className="modal-cab">
              <h2>{cajaAbierta.titulo}</h2>
              <button className="secundario" onClick={() => setCajaAbierta(null)}>✕</button>
            </div>
            <table className="tabla">
              <thead><tr><th>Colaborador</th><th>Área</th><th>Desempeño</th><th>Potencial</th><th>Clasificación</th></tr></thead>
              <tbody>
                {cajaAbierta.puntos.map((p) => (
                  <tr key={p.evaluacion_id}>
                    <td><Link to={`/evaluaciones/${p.evaluacion_id}`}>{p.nombre}</Link>
                      <div style={{ fontSize: 11.5, color: 'var(--gris-500)' }}>{p.codigo}</div></td>
                    <td>{p.area}</td>
                    <td><b>{p.desempeno}</b></td>
                    <td><b>{p.potencial}</b></td>
                    <td>
                      <span className={`etiqueta-estado ${CLAS[p.clasificacion]?.[0] || 'et-sin'}`}>
                        {CLAS[p.clasificacion]?.[1] || p.clasificacion || '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
