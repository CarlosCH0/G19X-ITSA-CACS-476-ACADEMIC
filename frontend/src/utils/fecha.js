const FORMATO_FECHA = new Intl.DateTimeFormat('es-MX', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
})

const FORMATO_HORA = new Intl.DateTimeFormat('es-MX', {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
})

function convertirFecha(valor) {
  if (valor instanceof Date) return Number.isNaN(valor.getTime()) ? null : valor
  if (typeof valor !== 'string' || !valor) return null

  const soloFecha = valor.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  const fecha = soloFecha
    ? new Date(Number(soloFecha[1]), Number(soloFecha[2]) - 1, Number(soloFecha[3]))
    : new Date(valor)

  return Number.isNaN(fecha.getTime()) ? null : fecha
}

export function formatearFecha(valor) {
  const fecha = convertirFecha(valor)
  if (!fecha) return '—'

  const partes = Object.fromEntries(
    FORMATO_FECHA.formatToParts(fecha).map(({ type, value }) => [type, value]),
  )
  return `${partes.day}/${partes.month}/${partes.year}`
}

export function formatearFechaHora(valor) {
  const fecha = convertirFecha(valor)
  if (!fecha) return '—'
  return `${formatearFecha(fecha)}, ${FORMATO_HORA.format(fecha)}`
}
