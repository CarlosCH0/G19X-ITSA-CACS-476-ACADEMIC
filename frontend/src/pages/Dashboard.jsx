import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { formatearFechaHora } from '../utils/fecha.js'

const ETIQUETAS_CLASIFICACION = {
  alto_potencial: ['et-hipo', 'Alto potencial'],
  en_desarrollo: ['et-desarrollo', 'En desarrollo'],
  estandar: ['et-estandar', 'Estándar'],
  no_evaluable: ['et-noevaluable', 'No evaluable'],
}

function GraficaLinea({ puntos }) {
  if (!puntos.length) return <p className="subtitulo">Sin datos de evolución.</p>
  const ancho = 560, alto = 150, margen = 28
  const valores = puntos.map((p) => p.promedio)
  const mn = Math.min(...valores) - 3, mx = Math.max(...valores) + 3
  const x = (i) => margen + (i * (ancho - margen * 2)) / Math.max(puntos.length - 1, 1)
  const y = (v) => alto - margen - ((v - mn) / Math.max(mx - mn, 1)) * (alto - margen * 2)
  const ruta = puntos.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.promedio)}`).join(' ')
  return (
    <svg className="svg-linea" viewBox={`0 0 ${ancho} ${alto}`} preserveAspectRatio="none">
      <line x1={margen} y1={alto - margen} x2={ancho - margen} y2={alto - margen} stroke="#cfd8dc" />
      {puntos.map((p, i) => (
        <g key={p.periodo}>
          <circle cx={x(i)} cy={y(p.promedio)} r="4" fill="#2e5395" />
          <text x={x(i)} y={alto - 8} textAnchor="middle" fontSize="10" fill="#78909c">{p.periodo}</text>
          <text x={x(i)} y={y(p.promedio) - 9} textAnchor="middle" fontSize="10" fill="#1f3864">{p.promedio}</text>
        </g>
      ))}
      <path d={ruta} fill="none" stroke="#2e5395" strokeWidth="2.5" />
    </svg>
  )
}

export default function Dashboard() {
  const { puede } = useAuth()
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState('')
  const [errorExportacion, setErrorExportacion] = useState('')

  useEffect(() => {
    api.get('/api/reportes/dashboard').then(setDatos).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="error">{error}</div>
  if (!datos) return <p className="subtitulo">Cargando indicadores…</p>

  const { kpis, distribucion_clasificacion: dist, promedios_por_area: areas, top_alto_potencial: top, evolucion_periodos: evolucion } = datos
  const maxDist = Math.max(...Object.values(dist), 1)
  const exportarResultados = async (formato) => {
    setErrorExportacion('')
    try {
      const parametros = { periodo: datos.periodo }
      if (formato === 'excel') {
        await api.descargarExcel('/api/reportes/export/evaluaciones.xlsx', parametros)
      } else {
        await api.descargarCsv('/api/reportes/export/evaluaciones.csv', parametros)
      }
    } catch (err) {
      setErrorExportacion(err.message)
    }
  }

  return (
    <div>
      <h1 className="titulo">Panel de talento</h1>
      <p className="subtitulo">
        Resumen general del periodo <b>{datos.periodo || '—'}</b> · Última actualización:{' '}
        {formatearFechaHora(datos.generado_en)}
      </p>

      <div className="tarjetas">
        <div className="tarjeta" title="Personas activas registradas en el sistema"><div className="etiqueta">Colaboradores activos</div><div className="valor">{kpis.colaboradores_activos}</div></div>
        <div className="tarjeta" title="Evaluaciones ejecutadas en el periodo mostrado"><div className="etiqueta">Evaluaciones del periodo</div><div className="valor">{kpis.evaluaciones_periodo}</div></div>
        <div className="tarjeta" title="Colaboradores que alcanzaron la puntuación mínima para ser alto potencial"><div className="etiqueta">Alto potencial (HiPo)</div><div className="valor" style={{ color: 'var(--verde)' }}>{kpis.alto_potencial}</div></div>
        <div className="tarjeta" title="Resultados en espera de confirmación por un evaluador"><div className="etiqueta">Revisiones pendientes</div><div className="valor" style={{ color: 'var(--ambar)' }}>{kpis.revisiones_pendientes}</div></div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h2>Distribución por clasificación</h2>
          <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>Cuántos colaboradores quedaron en cada categoría tras la evaluación.</p>
          {Object.entries(dist).map(([clave, total]) => (
            <div className="factor" key={clave}>
              <div className="factor-cab">
                <span>{ETIQUETAS_CLASIFICACION[clave]?.[1] || clave}</span>
                <b>{total}</b>
              </div>
              <div className="barra"><div style={{ width: `${(total / maxDist) * 100}%` }} /></div>
            </div>
          ))}
        </div>

        <div className="panel">
          <h2>Evolución del promedio por periodo</h2>
          <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>Promedio general de las puntuaciones (escala 0 a 100) de todos los evaluados.</p>
          <GraficaLinea puntos={evolucion} />
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h2>Promedio de puntuación por área</h2>
          <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>Puntuación promedio (0 a 100) de los evaluados de cada área.</p>
          <table className="tabla">
            <thead><tr><th>Área</th><th>Evaluados</th><th>Promedio</th></tr></thead>
            <tbody>
              {areas.map((a) => (
                <tr key={a.area}><td>{a.area}</td><td>{a.evaluados}</td><td><b>{a.promedio}</b></td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <h2>Top talento de alto potencial</h2>
          <p className="subtitulo" style={{ margin: '-6px 0 12px' }}>Colaboradores de alto potencial ordenados por puntuación; haz clic en un nombre para ver su perfil.</p>
          <table className="tabla">
            <thead><tr><th>Colaborador</th><th>Área</th><th>Puntuación</th><th>Revisión</th></tr></thead>
            <tbody>
              {top.map((t) => (
                <tr key={t.evaluacion_id}>
                  <td><Link to={`/colaboradores/${t.colaborador_id}`}>{t.nombre}</Link></td>
                  <td>{t.area}</td>
                  <td><b>{t.puntuacion}</b></td>
                  <td>
                    <Link to={`/evaluaciones/${t.evaluacion_id}`}>
                      <span className={`etiqueta-estado ${t.estado_revision === 'confirmado' ? 'et-confirmado' : 'et-sin'}`}>
                        {t.estado_revision === 'confirmado' ? 'Confirmado' : 'Sin revisar'}
                      </span>
                    </Link>
                  </td>
                </tr>
              ))}
              {!top.length && <tr><td colSpan="4">Aún no hay colaboradores clasificados como alto potencial en este periodo.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      {puede('reportes.exportar') && (
        <>
          <div className="botones">
            <button onClick={() => exportarResultados('csv')}>
              ⬇ Exportar resultados (CSV)
            </button>
            <button className="secundario" onClick={() => exportarResultados('excel')}>
              ⬇ Exportar resultados (Excel)
            </button>
          </div>
          {errorExportacion && <div className="error" role="alert">{errorExportacion}</div>}
        </>
      )}
    </div>
  )
}
