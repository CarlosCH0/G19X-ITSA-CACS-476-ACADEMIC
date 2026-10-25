import assert from 'node:assert/strict'
import test from 'node:test'
import { formatearFecha, formatearFechaHora } from './fecha.js'

test('formatea una fecha ISO sin desplazar el día', () => {
  assert.equal(formatearFecha('2026-02-01'), '01/02/2026')
})

test('rechaza fechas de calendario inexistentes', () => {
  assert.equal(formatearFecha('2026-02-30'), '—')
  assert.equal(formatearFecha('2026-13-01'), '—')
})

test('representa valores vacíos e inválidos con un guion', () => {
  assert.equal(formatearFecha(''), '—')
  assert.equal(formatearFecha('no es una fecha'), '—')
  assert.equal(formatearFechaHora('2026-02-30'), '—')
})
