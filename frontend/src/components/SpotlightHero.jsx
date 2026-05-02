import { useRef, useState, useEffect } from 'react'

export default function SpotlightHero({ children, className = '' }) {
  const containerRef = useRef(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      setMousePos({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      })
    }
    const el = containerRef.current
    if (el) {
      el.addEventListener('mousemove', handleMouseMove)
      return () => el.removeEventListener('mousemove', handleMouseMove)
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${className}`}
      style={{
        '--spot-x': `${mousePos.x}px`,
        '--spot-y': `${mousePos.y}px`,
      }}
    >
      {/* Spotlight radial */}
      <div
        className="pointer-events-none absolute inset-0 opacity-20 transition-opacity duration-700"
        style={{
          background: `radial-gradient(600px circle at var(--spot-x) var(--spot-y), rgba(212, 168, 83, 0.12), transparent 60%)`,
        }}
      />
      {children}
    </div>
  )
}
