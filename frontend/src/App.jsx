import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Colaboradores from './pages/Colaboradores.jsx'
import ColaboradorDetalle from './pages/ColaboradorDetalle.jsx'
import Evaluaciones from './pages/Evaluaciones.jsx'
import EvaluacionDetalle from './pages/EvaluacionDetalle.jsx'
import Indicadores from './pages/Indicadores.jsx'
import Configuracion from './pages/Configuracion.jsx'
import Auditoria from './pages/Auditoria.jsx'
import Usuarios from './pages/Usuarios.jsx'

function RutaProtegida({ permiso, children }) {
  const { usuario, puede } = useAuth()
  if (!usuario) return <Navigate to="/login" replace />
  if (permiso && !puede(permiso)) {
    return (
      <div className="pagina">
        <div className="error">
          No tienes permisos para acceder a esta sección (se requiere «{permiso}»).
        </div>
      </div>
    )
  }
  return children
}

export default function App() {
  const { usuario } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={usuario ? <Layout /> : <Navigate to="/login" replace />}>
        <Route path="/" element={<RutaProtegida permiso="reportes.consultar"><Dashboard /></RutaProtegida>} />
        <Route path="/colaboradores" element={<RutaProtegida permiso="colaboradores.consultar"><Colaboradores /></RutaProtegida>} />
        <Route path="/colaboradores/:id" element={<RutaProtegida permiso="colaboradores.consultar"><ColaboradorDetalle /></RutaProtegida>} />
        <Route path="/evaluaciones" element={<RutaProtegida permiso="reportes.consultar"><Evaluaciones /></RutaProtegida>} />
        <Route path="/evaluaciones/:id" element={<RutaProtegida permiso="reportes.consultar"><EvaluacionDetalle /></RutaProtegida>} />
        <Route path="/indicadores" element={<RutaProtegida permiso="colaboradores.consultar"><Indicadores /></RutaProtegida>} />
        <Route path="/configuracion" element={<RutaProtegida permiso="configuracion.gestionar"><Configuracion /></RutaProtegida>} />
        <Route path="/auditoria" element={<RutaProtegida permiso="auditoria.consultar"><Auditoria /></RutaProtegida>} />
        <Route path="/usuarios" element={<RutaProtegida permiso="usuarios.gestionar"><Usuarios /></RutaProtegida>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
