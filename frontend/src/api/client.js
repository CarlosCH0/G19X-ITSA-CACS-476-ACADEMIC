// Cliente HTTP con token JWT y manejo de errores común (RF-01).
const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, { method = 'GET', body, params } = {}) {
  const url = new URL(BASE + path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    })
  }
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const respuesta = await fetch(url.pathname + url.search, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (respuesta.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('usuario')
    if (!window.location.hash.includes('/login')) window.location.hash = '#/login'
    throw new Error('Sesión expirada o no autenticado')
  }
  if (respuesta.status === 204) return null

  const texto = await respuesta.text()
  const datos = texto ? JSON.parse(texto) : null
  if (!respuesta.ok) {
    const detalle = Array.isArray(datos?.detail)
      ? datos.detail.map((d) => d.msg).join('. ')
      : datos?.detail || `Error ${respuesta.status}`
    throw new Error(detalle)
  }
  return datos
}

export const api = {
  get: (path, params) => request(path, { params }),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
  descargarCsv: async (path, params) => {
    const url = new URL(BASE + path, window.location.origin)
    if (params) Object.entries(params).forEach(([k, v]) => { if (v) url.searchParams.set(k, v) })
    const headers = {}
    const token = localStorage.getItem('token')
    if (token) headers['Authorization'] = `Bearer ${token}`
    const r = await fetch(url.pathname + url.search, { headers })
    if (!r.ok) throw new Error(`Error ${r.status}`)
    const blob = await r.blob()
    const enlace = document.createElement('a')
    enlace.href = window.URL.createObjectURL(blob)
    enlace.download = (r.headers.get('content-disposition') || '').split('"')[1] || 'reporte.csv'
    enlace.click()
  },
}
