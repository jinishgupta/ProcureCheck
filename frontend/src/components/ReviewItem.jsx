import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'

export default function ReviewItem({ item, onConfirm, onOverride }) {
  const urgencyColors = {
    high: 'border-l-crimson-500',
    medium: 'border-l-amber-500',
    low: 'border-l-noir-600',
  }

  // Parse confidence from reason field if not directly available
  const parseConfidenceFromReason = (reason) => {
    if (!reason) return 0
    // Match patterns like "Confidence 20%" or "confidence 0.20" or "20%"
    const percentMatch = reason.match(/confidence\s+(\d+)%/i)
    if (percentMatch) return parseInt(percentMatch[1]) / 100
    
    const decimalMatch = reason.match(/confidence\s+(0?\.\d+)/i)
    if (decimalMatch) return parseFloat(decimalMatch[1])
    
    return 0
  }

  const confidence = item.confidence || parseConfidenceFromReason(item.reason)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`border border-noir-800 bg-noir-900/60 border-l-4 ${urgencyColors[item.urgency]} hover:border-noir-700 transition-colors`}
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-mono text-amber-500 tracking-wider uppercase">{item.urgency} Priority</span>
            </div>
            <h4 className="font-syne font-semibold text-lg text-noir-50 mb-1">
              {item.criterion || 'Unknown Criterion'}
            </h4>
            <p className="text-sm text-noir-400 font-mono">{item.bidder || 'Unknown Bidder'}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-mono font-bold text-amber-400">
              {(confidence * 100).toFixed(0)}%
            </div>
            <span className="text-xs text-noir-500 font-mono">confidence</span>
          </div>
        </div>

        {/* Extracted Value */}
        <div className="border border-noir-800 bg-noir-850 p-4 mb-4">
          <span className="text-xs text-noir-500 font-mono block mb-2">EXTRACTED VALUE</span>
          <p className="text-base text-noir-200 font-newsreader">
            {item.extractedValue || item.extracted_value || 'Not found'}
          </p>
        </div>

        {/* Reason */}
        <div className="bg-noir-850 border border-noir-800 p-3 mb-5">
          <span className="text-xs text-noir-500 font-mono block mb-1">REASON</span>
          <p className="text-sm text-noir-300 font-newsreader">{item.reason || 'Requires manual verification'}</p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onConfirm?.(item.id)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-jade-900/40 border border-jade-700/40 text-jade-400 text-sm font-mono hover:bg-jade-900/60 transition-colors"
          >
            <CheckCircle2 className="w-4 h-4" />
            CONFIRM PASS
          </button>
          <button
            onClick={() => onOverride?.(item.id)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-crimson-900/40 border border-crimson-600/40 text-crimson-400 text-sm font-mono hover:bg-crimson-900/60 transition-colors"
          >
            <XCircle className="w-4 h-4" />
            MARK FAIL
          </button>
        </div>
      </div>
    </motion.div>
  )
}
