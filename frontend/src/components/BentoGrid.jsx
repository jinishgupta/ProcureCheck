import { motion } from 'framer-motion'
import { useRef, useState } from 'react'

export default function BentoGrid({ items }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-noir-800/50">
      {items.map((item, i) => (
        <BentoCell key={i} item={item} index={i} />
      ))}
    </div>
  )
}

function BentoCell({ item, index }) {
  const cellRef = useRef(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const [isHovered, setIsHovered] = useState(false)

  const handleMouseMove = (e) => {
    if (!cellRef.current) return
    const rect = cellRef.current.getBoundingClientRect()
    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  const spanClass =
    index === 0
      ? 'md:col-span-2'
      : index === 3
      ? 'md:col-span-2'
      : ''

  return (
    <motion.div
      ref={cellRef}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`relative bg-noir-900 p-6 md:p-8 lg:p-10 overflow-hidden group cursor-default ${spanClass}`}
    >
      {/* Spotlight on hover */}
      {isHovered && (
        <div
          className="pointer-events-none absolute inset-0 opacity-100 transition-opacity duration-500"
          style={{
            background: `radial-gradient(300px circle at ${mousePos.x}px ${mousePos.y}px, rgba(212, 168, 83, 0.06), transparent 60%)`,
          }}
        />
      )}

      {/* Icon */}
      <div className="w-10 h-10 border border-noir-700 flex items-center justify-center mb-5 text-amber-500 group-hover:border-amber-500/40 transition-colors duration-500">
        {item.icon}
      </div>

      {/* Content */}
      <h3 className="font-syne font-bold text-xl md:text-2xl text-noir-50 mb-3 tracking-tight">
        {item.title}
      </h3>
      <p className="text-sm md:text-base text-noir-300 leading-relaxed font-newsreader">
        {item.description}
      </p>

      {/* Corner accent */}
      <div className="absolute top-0 right-0 w-8 h-8 border-t border-r border-noir-700/50 group-hover:border-amber-500/20 transition-colors duration-700" />
    </motion.div>
  )
}
