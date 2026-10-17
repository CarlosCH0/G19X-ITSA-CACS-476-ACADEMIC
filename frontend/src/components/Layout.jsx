import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { api } from '../api/client.js'
import Logo from './Logo.jsx'

// El menu muestra solo las opciones permitidas para el rol del usuario.
const MENU = [
  { to: '/', etiqueta: 'Panel de control', permiso: 'reportes.consultar', exacto: true },
  { to: '/colaboradores', etiqueta: 'Colaboradores', permiso: 'colaboradores.consultar' },
  { to: '/evaluaciones', etiqueta: 'Evaluaciones', permiso: 'reportes.consultar' },
  { to: '/matriz', etiqueta: 'Matriz 9-box', permiso: 'reportes.consultar' },
  { to: '/comparador', etiqueta: 'Comparador', permiso: 'reportes.consultar' },
  { to: '/indicadores', etiqueta: 'Indicadores', permiso: 'colaboradores.consultar' },
  { to: '/carga-datos', etiqueta: 'Carga masiva', permiso: 'indicadores.gestionar' },
  { to: '/planes', etiqueta: 'Planes y sucesión', permiso: 'planes.consultar' },
  { to: '/configuracion', etiqueta: 'Criterios', permiso: 'configuracion.gestionar' },
  { to: '/usuarios', etiqueta: 'Usuarios', permiso: 'usuarios.gestionar' },
  { to: '/auditoria', etiqueta: 'Auditoría', permiso: 'auditoria.consultar' },
]

function CampanaAlertas() {
  const [alertas, setAlertas] = useState(null)
  const [abierta, setAbierta] = useState(false)

  // Las alertas se actualizan cada dos minutos. La bandera evita cambiar
  // el estado si el componente ya se cerro.
  useEffect(() => {
    let activo = true
    const cargar = () =>
      api.get('/api/reportes/alertas').then((a) => activo && setAlertas(a)).catch(() => {})
    cargar()
    const temporizador = setInterval(cargar, 120000)
    return () => { activo = false; clearInterval(temporizador) }
  }, [])

  if (!alertas) return null
  const criticas = alertas.items.filter((i) => i.total > 0)

  return (
    <div className="campana-wrap">
      <button
        className="campana"
        onClick={() => setAbierta(!abierta)}
        title="Centro de alertas"
        aria-label={`Alertas: ${alertas.total}`}
      >
        Alertas
        {alertas.total > 0 && <span className="campana-contador">{alertas.total}</span>}
      </button>
      {abierta && (
        <>
          <div className="campana-fondo" onClick={() => setAbierta(false)} />
          <div className="campana-panel">
            <div className="campana-cab">
              <b>Centro de alertas</b>
              <span style={{ fontSize: 11.5, color: 'var(--gris-500)' }}>
                Periodo {alertas.periodo || '—'}
              </span>
            </div>
            {criticas.length === 0 && (
              <div className="campana-item" style={{ color: 'var(--verde)' }}>
                ✔ Todo en orden: sin pendientes operativos.
              </div>
            )}
            {criticas.map((i) => (
              <div key={i.clave} className={`campana-item ${i.total > 0 ? 'con-pendiente' : ''}`}>
                <div className="campana-item-titulo">
                  <span>{i.titulo}</span><b>{i.total}</b>
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--gris-500)' }}>{i.detalle}</div>
              </div>
            ))}
            {alertas.revisiones_destacadas.length > 0 && (
              <div className="campana-pie">
                Pendientes principales: {alertas.revisiones_destacadas.slice(0, 3)
                  .map((r) => `${r.colaborador} (${r.puntuacion ?? '—'})`).join(' · ')}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default function Layout() {
  const { usuario, cerrarSesion, puede } = useAuth()
  const navegar = useNavigate()
  const [menuAbierto, setMenuAbierto] = useState(false)
  const [modoOscuro, setModoOscuro] = useState(() => localStorage.getItem('tema') === 'oscuro')

  useEffect(() => {
    document.documentElement.dataset.tema = modoOscuro ? 'oscuro' : 'claro'
    localStorage.setItem('tema', modoOscuro ? 'oscuro' : 'claro')
  }, [modoOscuro])

  useEffect(() => {
    if (!menuAbierto) return
    const cerrarConEscape = (evento) => {
      if (evento.key === 'Escape') setMenuAbierto(false)
    }
    window.addEventListener('keydown', cerrarConEscape)
    return () => window.removeEventListener('keydown', cerrarConEscape)
  }, [menuAbierto])

  const salir = () => {
    cerrarSesion()
    navegar('/login')
  }

  return (
    <div className="layout">
      {menuAbierto && (
        <button
          className="menu-fondo"
          type="button"
          aria-label="Cerrar menú"
          onClick={() => setMenuAbierto(false)}
        />
      )}
      <aside id="menu-principal" className={`sidebar ${menuAbierto ? 'abierto' : ''}`} aria-hidden={!menuAbierto}>
        <div className="marca">
          <Logo tamano={32} />
          <div className="marca-texto">
            <strong>Talento HiPo</strong>
            <span>Develop Talent &amp; Technology</span>
          </div>
        </div>
        <nav className="menu">
          {MENU.filter((m) => puede(m.permiso)).map((m) => (
            <NavLink key={m.to} to={m.to} end={m.exacto} onClick={() => setMenuAbierto(false)} className={({ isActive }) => (isActive ? 'activo' : '')}>
              {m.etiqueta}
            </NavLink>
          ))}
        </nav>
        <button
          className="tema-toggle"
          type="button"
          aria-pressed={modoOscuro}
          onClick={() => setModoOscuro(!modoOscuro)}
        >
          <span>Modo oscuro</span>
          <span className="tema-interruptor" aria-hidden="true"><span /></span>
        </button>
        <div className="pie">Sistema de Identificación de Talento de Alto Potencial · v1.1</div>
      </aside>
      <div className="contenido">
        <header className="topbar">
          <div className="topbar-inicio">
            <button
              className="menu-toggle"
              type="button"
              aria-label={menuAbierto ? 'Cerrar menú' : 'Abrir menú'}
              aria-expanded={menuAbierto}
              aria-controls="menu-principal"
              onClick={() => setMenuAbierto(!menuAbierto)}
            >
              <span /><span /><span />
            </button>
            <div style={{ fontWeight: 600, color: 'var(--azul-900)' }}>Analítica de personas</div>
          </div>
          <div className="usuario">
            {puede('reportes.consultar') && <CampanaAlertas />}
            <b>{usuario?.nombre}</b>
            <span className="rol">{usuario?.rol}</span>
            <button className="secundario" style={{ marginLeft: 14 }} onClick={salir}>
              Cerrar sesión
            </button>
          </div>
        </header>
        <main className="pagina">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
