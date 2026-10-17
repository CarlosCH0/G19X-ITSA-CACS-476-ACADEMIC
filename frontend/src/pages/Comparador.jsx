import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'

const CLAS = {
  alto_potencial: ['et-hipo', 'Alto potencial'],
  en_desarrollo: ['et-desarrollo', 'En desarrollo'],
  estandar: ['et-estandar', 'Estándar'],
  no_evaluable: ['et-noevaluable', 'No evaluable'],
}
const COLORES = ['#60a5fa', '#34d399', '#fbbf24', '#fb7185', '#c084fc', '#22d3ee']

function Radar({ indicadores, colaboradores }) {
  const ancho = 560, alto = 500, cx = ancho / 2, cy = alto / 2, radio = 145
  const indicadoresRadar = indicadores.filter((ind) =>
    colaboradores.every((colaborador) => ind.radar?.[String(colaborador.id)] != null)
  )
  const colaboradoresRadar = colaboradores
  const n = indicadoresRadar.length
  if (n < 3) {
    return (
      <p className="radar-aviso">
        Se necesitan al menos 3 indicadores con mediciones válidas para todos los colaboradores
        seleccionados. No se dibujan datos faltantes como si fueran cero.
      </p>
    )
  }

  const angulo = (i) => (Math.PI * 2 * i) / n - Math.PI / 2
  const punto = (i, valor) => {
    const r = (valor / 100) * radio
    return [cx + r * Math.cos(angulo(i)), cy + r * Math.sin(angulo(i))]
  }
  const etiquetaPos = (i) => {
    const r = radio + 58
    return [cx + r * Math.cos(angulo(i)), cy + r * Math.sin(angulo(i))]
  }
  const lineasEtiqueta = (nombre) => {
    const palabras = nombre.split(/\s+/)
    const lineas = []
    let linea = ''
    palabras.forEach((palabra) => {
      if (linea && `${linea} ${palabra}`.length > 14) {
        lineas.push(linea)
        linea = palabra
      } else {
        linea = linea ? `${linea} ${palabra}` : palabra
      }
    })
    if (linea) lineas.push(linea)
    return lineas.slice(0, 3)
  }

  return (
    <div>
      <svg
        className="radar-grafico"
        viewBox={`0 0 ${ancho} ${alto}`}
        role="img"
        aria-label={`Comparación radial de ${n} indicadores para ${colaboradoresRadar.length} colaboradores`}
      >
        {[20, 40, 60, 80, 100].map((nivel) => (
          <g key={nivel}>
            <polygon
              points={indicadoresRadar.map((_, i) => punto(i, nivel).join(',')).join(' ')}
              className="radar-rejilla"
            />
            <text x={cx + 4} y={cy - (nivel / 100) * radio - 3} className="radar-escala">
              {nivel}
            </text>
          </g>
        ))}
        {indicadoresRadar.map((ind, i) => {
          const [x, y] = punto(i, 100)
          const [ex, ey] = etiquetaPos(i)
          const lineas = lineasEtiqueta(ind.nombre)
          return (
            <g key={ind.codigo}>
              <line x1={cx} y1={cy} x2={x} y2={y} className="radar-eje" />
              <text x={ex} y={ey} textAnchor="middle" className="radar-etiqueta">
                <title>{ind.nombre}</title>
                {lineas.map((linea, indice) => (
                  <tspan key={linea} x={ex} dy={indice === 0 ? `${-(lineas.length - 1) * 6}px` : '12px'}>
                    {linea}
                  </tspan>
                ))}
              </text>
            </g>
          )
        })}
        {colaboradoresRadar.map((c) => {
          const idx = colaboradores.findIndex((colaborador) => colaborador.id === c.id)
          const color = COLORES[idx % COLORES.length]
          const puntos = indicadoresRadar.map((ind, i) =>
            punto(i, ind.radar[String(c.id)]).join(',')
          ).join(' ')
          return (
            <g key={c.id}>
              <polygon points={puntos} fill={color} fillOpacity="0.22" stroke={color} strokeWidth="3" strokeLinejoin="round" />
              {indicadoresRadar.map((ind, i) => {
                const [x, y] = punto(i, ind.radar[String(c.id)])
                return (
                  <circle
                    key={ind.codigo}
                    cx={x}
                    cy={y}
                    r="4"
                    fill={color}
                    stroke="var(--radar-point-border)"
                    strokeWidth="1.5"
                  />
                )
              })}
            </g>
          )
        })}
      </svg>
      {n < indicadores.length && (
        <p className="radar-aviso">
          Se muestran solo {n} indicadores con mediciones válidas para todos los colaboradores
          seleccionados; los indicadores faltantes se excluyen, no se representan como cero.
        </p>
      )}
    </div>
  )
}

export default function Comparador() {
  const [colaboradores, setColaboradores] = useState([])
  const [periodos, setPeriodos] = useState([])
  const [seleccion, setSeleccion] = useState([])
  const [periodo, setPeriodo] = useState('')
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/colaboradores', { tamanio: 100 }).then((p) => setColaboradores(p.items)).catch(() => {})
    api.get('/api/indicadores/periodos').then(setPeriodos).catch(() => {})
  }, [])

  useEffect(() => {
    if (seleccion.length >= 2) {
      api.get('/api/reportes/comparar', { ids: seleccion.join(','), ...(periodo && { periodo }) })
        .then(setDatos).catch((e) => setError(e.message))
    } else {
      setDatos(null)
    }
  }, [seleccion, periodo])

  const toggle = (id) => {
    setError('')
    setSeleccion((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id)
        : prev.length >= 6 ? prev : [...prev, id]
    )
  }

  const comparados = useMemo(
    () => (datos ? datos.colaboradores : []),
    [datos]
  )

  return (
    <div>
      <h1 className="titulo">Comparador de colaboradores</h1>
      <p className="subtitulo">
        Elige de 2 a 6 colaboradores para comparar sus resultados. El radar usa una escala fija de 0 a
        100; la tabla muestra los valores registrados y su posición frente al grupo seleccionado.
      </p>
      {error && <div className="error">{error}</div>}

      <div className="filtros">
        <select value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
          <option value="">Periodo más reciente</option>
          {periodos.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <span style={{ fontSize: 13, color: 'var(--gris-700)' }}>
          Seleccionados: <b>{seleccion.length}</b> de 6 (máximo) · Solo se usan mediciones válidas
        </span>
        {seleccion.length > 0 && (
          <button className="secundario" onClick={() => setSeleccion([])}>Limpiar</button>
        )}
      </div>

      <div className="panel">
        <h2>Selecciona colaboradores</h2>
        <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>Haz clic en los nombres que quieras comparar; vuelve a hacer clic para quitarlos.</p>
        <div className="selector-chips">
          {colaboradores.map((c) => {
            const idx = seleccion.indexOf(c.id)
            const activo = idx >= 0
            return (
              <button
                key={c.id}
                className={`chip ${activo ? 'chip-activo' : ''}`}
                onClick={() => toggle(c.id)}
                style={activo ? { borderColor: COLORES[idx % COLORES.length], background: `${COLORES[idx % COLORES.length]}18` } : {}}
              >
                {activo && <span className="chip-punto" style={{ background: COLORES[idx % COLORES.length] }} />}
                {c.codigo} · {c.nombre}
              </button>
            )
          })}
        </div>
      </div>

      {datos && comparados.length >= 2 && (
        <>
          <div className="grid-2">
            <div className="panel">
              <h2>Perfil comparado (gráfico radar)</h2>
              <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>Cada eje usa una escala comparable de 0 a 100; cuanto más lejos del centro, mejor es el resultado.</p>
              <Radar indicadores={datos.indicadores} colaboradores={comparados} />
              <div className="leyenda-radar">
                {comparados.map((c, i) => (
                  <span key={c.id}>
                    <span className="chip-punto" style={{ background: COLORES[i % COLORES.length] }} />
                    <Link to={`/colaboradores/${c.id}`}>{c.nombre}</Link>
                    {c.evaluacion && (
                      <span className={`etiqueta-estado ${CLAS[c.evaluacion.clasificacion]?.[0] || 'et-sin'}`} style={{ marginLeft: 6 }}>
                        {c.evaluacion.puntuacion ?? '—'}
                      </span>
                    )}
                  </span>
                ))}
              </div>
            </div>

            <div className="panel">
              <h2>Puntuación y clasificación del periodo</h2>
              <table className="tabla">
                <thead><tr><th>Colaborador</th><th>Área</th><th>Puntuación</th><th>Clasificación</th></tr></thead>
                <tbody>
                  {comparados.map((c) => (
                    <tr key={c.id}>
                      <td><Link to={`/colaboradores/${c.id}`}>{c.nombre}</Link></td>
                      <td>{c.area}</td>
                      <td><b>{c.evaluacion?.puntuacion ?? '—'}</b></td>
                      <td>
                        <span className={`etiqueta-estado ${CLAS[c.evaluacion?.clasificacion]?.[0] || 'et-sin'}`}>
                          {CLAS[c.evaluacion?.clasificacion]?.[1] || 'Sin evaluación'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel">
            <h2>Detalle por indicador</h2>
            <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>Valor registrado y, debajo, su posición (0 a 100) frente a los comparados.</p>
            <div style={{ overflowX: 'auto' }}>
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Indicador</th><th>Tipo</th>
                    {comparados.map((c) => <th key={c.id}>{c.codigo}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {datos.indicadores.map((ind) => (
                    <tr key={ind.codigo}>
                      <td><b>{ind.nombre}</b><div style={{ fontSize: 11, color: 'var(--gris-500)' }}>{ind.codigo}</div></td>
                      <td style={{ textTransform: 'capitalize' }}>{ind.tipo}</td>
                      {comparados.map((c) => {
                        const valor = ind.valores[String(c.id)]
                        const norm = ind.normalizados[String(c.id)]
                        return (
                          <td key={c.id}>
                            {valor !== undefined ? (
                              <>
                                <b>{valor}</b>
                                <div className="barra" style={{ width: 90, marginTop: 4 }}>
                                  <div style={{ width: `${norm ?? 0}%` }} />
                                </div>
                              </>
                            ) : <span style={{ color: 'var(--gris-500)' }}>s/d</span>}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="subtitulo" style={{ marginTop: 10 }}>
              «s/d» significa que no hay dato válido en el periodo. Las barras comparan solo a los
              seleccionados: el mejor del grupo en cada indicador llega a 100.
            </p>
          </div>
        </>
      )}

      {seleccion.length > 0 && seleccion.length < 2 && (
        <div className="aviso">Selecciona al menos 2 colaboradores para comparar.</div>
      )}
    </div>
  )
}
