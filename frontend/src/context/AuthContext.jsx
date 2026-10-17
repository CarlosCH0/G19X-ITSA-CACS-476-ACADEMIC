import React, { createContext, useContext, useMemo, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(() => {
    const guardado = localStorage.getItem('usuario')
    return guardado ? JSON.parse(guardado) : null
  })

  const valor = useMemo(
    () => ({
      usuario,
      puede: (permiso) => Boolean(usuario?.permisos?.includes(permiso)),
      iniciarSesion: ({ access_token, usuario: u }) => {
        localStorage.setItem('token', access_token)
        localStorage.setItem('usuario', JSON.stringify(u))
        setUsuario(u)
      },
      cerrarSesion: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('usuario')
        setUsuario(null)
      },
    }),
    [usuario]
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
