import { motion } from 'framer-motion'

export default function ConfidenceBar({ extraction = 0, ocr = 0, retrieval = 0, llm = 0, size = 'md' }) {
  const final = extraction * ocr * retrieval * llm
  const signals = [
    { label: 'Extraction', value: extraction, color: 'bg-amber-500' },
    { label: 'OCR', value: ocr, color: 'bg-jade-500' },
    { label: 'Retrieval', value: retrieval, color: 'bg-noir-300' },
    { label: 'LLM Logprob', value: llm, color: 'bg-amber-400' },
  ]

  const height = size === 'sm' ? 'h-1' : 'h-1.5'

  return (
    <div className="space-y-2">
      {signals.map((signal, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs text-noir-400 w-20 shrink-0 font-mono">{signal.label}</span>
          <div className={`flex-1 bg-noir-800 ${height} overflow-hidden`}>
            <motion.div
              className={`${height} ${signal.color}`}
              initial={{ width: 0 }}
              animate={{ width: `${signal.value * 100}%` }}
              transition={{ duration: 0.8, delay: i * 0.1, ease: 'easeOut' }}
            />
          </div>
          <span className="text-xs text-noir-300 font-mono w-10 text-right">
            {(signal.value * 100).toFixed(0)}%
          </span>
        </div>
      ))}
      <div className="flex items-center gap-3 pt-1 border-t border-noir-800">
        <span className="text-xs text-noir-200 w-20 shrink-0 font-mono font-semibold">Final</span>
        <div className={`flex-1 bg-noir-800 h-2 overflow-hidden`}>
          <motion.div
            className={`h-2 ${final >= 0.9 ? 'bg-jade-500' : final >= 0.5 ? 'bg-amber-500' : 'bg-crimson-500'}`}
            initial={{ width: 0 }}
            animate={{ width: `${final * 100}%` }}
            transition={{ duration: 1, delay: 0.5, ease: 'easeOut' }}
          />
        </div>
        <span className="text-xs text-noir-100 font-mono font-semibold w-10 text-right">
          {(final * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  )
}
