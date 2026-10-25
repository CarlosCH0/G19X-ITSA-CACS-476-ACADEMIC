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

  // Si ya hay una sesion activa, se muestra directamente el inicio.
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
        <p>Sistema de Identificación de Talento de Alto Potencial</p>
        {error && <div className="error" role="alert">{error}</div>}
        <form onSubmit={enviar}>
          <div>
            <label htmlFor="login-correo">Correo electrónico</label>
            <input
              id="login-correo"
              type="email"
              name="correo"
              autoComplete="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              placeholder="usuario@develop.com.mx"
              required
              autoFocus
            />
          </div>
          <div>
            <label htmlFor="login-password">Contraseña</label>
            <input
              id="login-password"
              type="password"
              name="password"
              autoComplete="current-password"
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
      </div>
    </div>
  )
}
