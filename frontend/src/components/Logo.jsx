/**
 * Logo HiPo — icono vectorial oficial del sistema (MVP).
 *
 * Matriz 9-box minimalista: solo el cuadrante superior derecho
 * (alto desempeño × alto potencial) se destaca en ámbar, con un destello
 * que representa al colaborador identificado.
 * Réplica exacta de `logo/logo-icono.svg`.
 */
export default function Logo({ tamano = 28, conFondo = true, className = '' }) {
  const celdas = [
    { x: 78, y: 78, hipo: true },
    { x: 206, y: 78 }, { x: 334, y: 78 },
    { x: 78, y: 206 }, { x: 206, y: 206 }, { x: 334, y: 206 },
    { x: 78, y: 334 }, { x: 206, y: 334 }, { x: 334, y: 334 },
  ]
  return (
    <svg
      width={tamano}
      height={tamano}
      viewBox="0 0 512 512"
      role="img"
      aria-label="Logo HiPo — Talento de Alto Potencial"
      className={className}
    >
      {conFondo && <rect width="512" height="512" rx="112" fill="#1f3864" />}
      {celdas.map((c) => (
        <rect
          key={`${c.x}-${c.y}`}
          x={c.x}
          y={c.y}
          width="100"
          height="100"
          rx="22"
          fill={c.hipo ? '#f9a825' : '#2e5395'}
        />
      ))}
      <path
        d="M384 94 Q391.5 120.5 418 128 Q391.5 135.5 384 162 Q376.5 135.5 350 128 Q376.5 120.5 384 94 Z"
        fill={conFondo ? '#ffffff' : '#1f3864'}
      />
    </svg>
  )
}
