import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, AlertTriangle, CheckCircle2, Hash } from 'lucide-react'

export default function CriterionCard({ criterion, index }) {
  const [expanded, setExpanded] = useState(false)

  const typeColors = {
    financial: 'text-amber-500 border-amber-500/20',
    technical: 'text-jade-500 border-jade-500/20',
    certification: 'text-noir-200 border-noir-500/20',
    experience: 'text-amber-400 border-amber-400/20',
  }

  const colorClass = typeColors[criterion.type] || typeColors.technical

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="border border-noir-800 bg-noir-900/60 hover:border-noir-700 transition-colors duration-300"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-4 p-4 text-left"
      >
        {/* Mandatory indicator */}
        <div className={`w-1.5 h-8 shrink-0 ${criterion.mandatory ? 'bg-amber-500' : 'bg-noir-700'}`} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-mono px-2 py-0.5 border ${colorClass}`}>
              {criterion.type}
            </span>
            {criterion.mandatory && (
              <span className="text-xs font-mono text-amber-500">MANDATORY</span>
            )}
            {criterion.unresolvedRef && (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            )}
          </div>
          <p className="text-sm text-noir-100 font-newsreader truncate">{criterion.field}</p>
        </div>

        <ChevronDown
          className={`w-4 h-4 text-noir-500 transition-transform duration-300 shrink-0 ${
            expanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-0 border-t border-noir-800/50 space-y-3">
              <div className="pt-3 grid grid-cols-2 gap-3">
                <div>
                  <span className="text-xs text-noir-500 font-mono block mb-1">REQUIREMENT</span>
                  <p className="text-sm text-noir-200 font-newsreader">{criterion.requirement}</p>
                </div>
                <div>
                  <span className="text-xs text-noir-500 font-mono block mb-1">SOURCE</span>
                  <p className="text-sm text-noir-300 font-mono">{criterion.source}</p>
                </div>
              </div>

              {criterion.unresolvedRef && (
                <div className="flex items-start gap-2 p-3 bg-amber-900/20 border border-amber-500/20">
                  <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-amber-400 font-mono mb-0.5">UNRESOLVED REFERENCE</p>
                    <p className="text-sm text-noir-300 font-newsreader">{criterion.unresolvedRef}</p>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
