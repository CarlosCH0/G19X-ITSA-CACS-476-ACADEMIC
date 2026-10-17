const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, { method = 'GET', body, params } = {}) {
  const url = new URL(BASE + path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    })
  }
  const token = localStorage.getItem('token')
  const esFormulario = typeof FormData !== 'undefined' && body instanceof FormData
  const headers = esFormulario ? {} : { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const respuesta = await fetch(url.pathname + url.search, {
    method,
    headers,
    body: body === undefined ? undefined : esFormulario ? body : JSON.stringify(body),
  })

  if (respuesta.status === 401) {
    // Si la sesion vencio o el token no sirve, se limpia y se vuelve al inicio.
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

async function descargarArchivo(path, params, nombrePredeterminado) {
  const url = new URL(BASE + path, window.location.origin)
  if (params) Object.entries(params).forEach(([k, v]) => { if (v) url.searchParams.set(k, v) })
  const headers = {}
  const token = localStorage.getItem('token')
  if (token) headers['Authorization'] = `Bearer ${token}`
  const respuesta = await fetch(url.pathname + url.search, { headers })
  if (!respuesta.ok) {
    const tipoContenido = respuesta.headers.get('content-type') || ''
    let mensaje = `Error ${respuesta.status}`
    if (tipoContenido.includes('application/json')) {
      const datos = await respuesta.json()
      if (typeof datos?.detail === 'string') mensaje = datos.detail
    }
    throw new Error(mensaje)
  }
  const blob = await respuesta.blob()
  const enlace = document.createElement('a')
  enlace.href = window.URL.createObjectURL(blob)
  enlace.download = (respuesta.headers.get('content-disposition') || '').split('"')[1] || nombrePredeterminado
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  window.setTimeout(() => window.URL.revokeObjectURL(enlace.href), 1000)
}

export const api = {
  get: (path, params) => request(path, { params }),
  post: (path, body) => request(path, { method: 'POST', body }),
  postArchivo: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
  descargarCsv: (path, params) => descargarArchivo(path, params, 'reporte.csv'),
  descargarExcel: (path, params) => descargarArchivo(path, params, 'reporte.xlsx'),
}
