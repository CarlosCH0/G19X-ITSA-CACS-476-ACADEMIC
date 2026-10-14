import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import Logo from '../components/Logo.jsx'

export default function Login() {
  const { iniciarSesion, usuario } = useAuth()
  const navegar = useNavigate()
  const [correo, setCorreo] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  // Redirección declarativa: si ya hay sesión, no se muestra el formulario.
  if (usuario) return <Navigate to="/" replace />

  const enviar = async (e) => {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const respuesta = await api.post('/api/auth/login', { correo, password })
      iniciarSesion(respuesta)
      navegar('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="login-vista">
      <div className="login-caja">
        <div className="login-logo">
          <Logo tamano={54} />
        </div>
        <h1>
          Talento HiPo<span className="punto-ambar">.</span>
        </h1>
        <p>Sistema para identificar talento de alto potencial</p>
        {error && <div className="error">{error}</div>}
        <form onSubmit={enviar}>
          <div>
            <label>Correo electrónico</label>
            <input
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              placeholder="usuario@develop.com.mx"
              required
              autoFocus
            />
          </div>
          <div>
            <label>Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <button type="submit" disabled={cargando}>
            {cargando ? 'Verificando…' : 'Iniciar sesión'}
          </button>
        </form>
        <div className="login-nota">
          Usuario de prueba: admin@develop.com.mx
          (contraseña: Admin123!).
        </div>
      </div>
    </div>
  )
}
