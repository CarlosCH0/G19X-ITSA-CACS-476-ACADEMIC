import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import Logo from './Logo.jsx'

const MENU = [
  { to: '/', etiqueta: 'Resumen', permiso: 'reportes.consultar', exacto: true },
  { to: '/colaboradores', etiqueta: 'Colaboradores', permiso: 'colaboradores.consultar' },
  { to: '/evaluaciones', etiqueta: 'Evaluaciones', permiso: 'reportes.consultar' },
  { to: '/indicadores', etiqueta: 'Indicadores', permiso: 'colaboradores.consultar' },
  { to: '/configuracion', etiqueta: 'Configuración', permiso: 'configuracion.gestionar' },
  { to: '/usuarios', etiqueta: 'Usuarios', permiso: 'usuarios.gestionar' },
  { to: '/auditoria', etiqueta: 'Auditoría', permiso: 'auditoria.consultar' },
]

export default function Layout() {
  const { usuario, cerrarSesion, puede } = useAuth()
  const navegar = useNavigate()

  const salir = () => {
    cerrarSesion()
    navegar('/login')
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="marca">
          <Logo tamano={32} />
          <div className="marca-texto">
            <strong>Talento HiPo</strong>
            <span>Develop Talent &amp; Technology</span>
          </div>
        </div>
        <nav className="menu">
          {MENU.filter((m) => puede(m.permiso)).map((m) => (
            <NavLink key={m.to} to={m.to} end={m.exacto} className={({ isActive }) => (isActive ? 'activo' : '')}>
              {m.etiqueta}
            </NavLink>
          ))}
        </nav>
        <div className="pie">Sistema para identificar talento de alto potencial · MVP</div>
      </aside>
      <div className="contenido">
        <header className="topbar">
          <div style={{ fontWeight: 600, color: 'var(--azul-900)' }}>Resumen operativo</div>
          <div className="usuario">
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
