import { motion, useInView } from 'framer-motion'
import { useRef, useState, useEffect } from 'react'

export default function StatsCard({ value, label, suffix = '', icon }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    if (!isInView) return

    const numericValue = parseInt(value, 10)
    if (isNaN(numericValue)) {
      setDisplayValue(value)
      return
    }

    let start = 0
    const duration = 1500
    const startTime = performance.now()

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = Math.floor(eased * numericValue)
      setDisplayValue(current)
      if (progress < 1) requestAnimationFrame(animate)
    }

    requestAnimationFrame(animate)
  }, [isInView, value])

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="relative border border-noir-800 bg-noir-900/60 p-6 group hover:border-noir-700 transition-colors duration-500"
    >
      {/* Shimmer line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-noir-800 overflow-hidden">
        <motion.div
          className="h-full w-1/3 bg-amber-500/30"
          animate={{ x: ['-100%', '400%'] }}
          transition={{ duration: 3, repeat: Infinity, repeatDelay: 2, ease: 'easeInOut' }}
        />
      </div>

      <div className="flex items-start justify-between mb-3">
        <div className="text-amber-500/50">{icon}</div>
      </div>

      <div className="font-syne font-bold text-3xl text-noir-50 tracking-tight mb-1">
        {displayValue}{suffix}
      </div>
      <div className="text-sm text-noir-400 font-newsreader">{label}</div>
    </motion.div>
  )
}
