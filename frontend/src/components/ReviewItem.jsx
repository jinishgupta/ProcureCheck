import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, RotateCw, Eye } from 'lucide-react'
import ConfidenceBar from './ConfidenceBar'

export default function ReviewItem({ item, onConfirm, onOverride, onRescan }) {
  const urgencyColors = {
    high: 'border-l-crimson-500',
    medium: 'border-l-amber-500',
    low: 'border-l-noir-500',
  }

  // Safely access signals with defaults
  const signals = item.signals || { extraction: 0, ocr: 0, retrieval: 0, llm: 0 }
  const confidence = item.confidence || 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`border border-noir-800 bg-noir-900/60 border-l-2 ${urgencyColors[item.urgency]} hover:border-noir-700 transition-colors`}
    >
      <div className="p-6 md:p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-mono text-amber-500 tracking-wider">REVIEW REQUIRED</span>
            </div>
            <h4 className="font-syne font-semibold text-noir-50 mb-0.5">
              {item.criterion || 'Unknown Criterion'}
            </h4>
            <p className="text-sm text-noir-400 font-mono">{item.bidder || 'Unknown Bidder'}</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-mono font-bold text-amber-400">
              {(confidence * 100).toFixed(0)}%
            </div>
            <span className="text-xs text-noir-500 font-mono">confidence</span>
          </div>
        </div>

        {/* Details */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="border border-noir-800 p-3">
            <span className="text-xs text-noir-500 font-mono block mb-1">EXTRACTED</span>
            <p className="text-sm text-noir-200 font-newsreader">
              {item.extractedValue || item.extracted_value || 'Not found'}
            </p>
          </div>
          <div className="border border-noir-800 p-3">
            <span className="text-xs text-noir-500 font-mono block mb-1">REQUIRED</span>
            <p className="text-sm text-noir-200 font-newsreader">
              {item.requiredValue || item.required_value || 'N/A'}
            </p>
          </div>
        </div>

        {/* Confidence breakdown */}
        <div className="mb-5">
          <ConfidenceBar
            extraction={signals.extraction || 0}
            ocr={signals.ocr || 0}
            retrieval={signals.retrieval || 0}
            llm={signals.llm || 0}
            size="sm"
          />
        </div>

        {/* Reason */}
        <div className="bg-noir-850 border border-noir-800 p-3 mb-5">
          <span className="text-xs text-noir-500 font-mono block mb-1">REASON FOR REVIEW</span>
          <p className="text-sm text-noir-300 font-newsreader">{item.reason || 'Requires manual verification'}</p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onConfirm?.(item.id)}
            className="flex items-center gap-2 px-4 py-2 bg-jade-900/40 border border-jade-700/40 text-jade-400 text-xs font-mono hover:bg-jade-900/60 transition-colors"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            CONFIRM PASS
          </button>
          <button
            onClick={() => onOverride?.(item.id)}
            className="flex items-center gap-2 px-4 py-2 bg-crimson-900/40 border border-crimson-600/40 text-crimson-400 text-xs font-mono hover:bg-crimson-900/60 transition-colors"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            OVERRIDE FAIL
          </button>
          <button
            onClick={() => onRescan?.(item.id)}
            className="flex items-center gap-2 px-4 py-2 border border-noir-700 text-noir-300 text-xs font-mono hover:border-noir-500 hover:text-noir-100 transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
            RE-SCAN
          </button>
          <button className="ml-auto flex items-center gap-2 px-3 py-2 text-noir-400 text-xs font-mono hover:text-noir-200 transition-colors">
            <Eye className="w-3.5 h-3.5" />
            VIEW SOURCE
          </button>
        </div>
      </div>
    </motion.div>
  )
}
