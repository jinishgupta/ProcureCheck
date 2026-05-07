import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ConfidenceBar from './ConfidenceBar'

export default function MatrixCell({ data, bidderName, criterionName }) {
  const [showDetail, setShowDetail] = useState(false)

  const verdictStyles = {
    PASS: 'bg-jade-900/60 border-jade-700/40 text-jade-400',
    FAIL: 'bg-crimson-900/60 border-crimson-600/40 text-crimson-400',
    REVIEW: 'bg-amber-900/40 border-amber-700/40 text-amber-400',
  }

  const verdictDot = {
    PASS: 'bg-jade-500',
    FAIL: 'bg-crimson-500',
    REVIEW: 'bg-amber-500',
  }

  return (
    <>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setShowDetail(true)}
        className={`relative w-full aspect-square flex flex-col items-center justify-center border transition-colors duration-300 cursor-pointer ${verdictStyles[data.verdict]}`}
      >
        <div className={`w-2 h-2 mb-2 ${verdictDot[data.verdict]}`} />
        <span className="text-xs font-mono font-semibold">{data.verdict}</span>
      </motion.button>

      {/* Detail panel overlay */}
      <AnimatePresence>
        {showDetail && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-end"
            onClick={() => setShowDetail(false)}
          >
            <div className="absolute inset-0 bg-noir-950/70 backdrop-blur-sm" />
            <motion.div
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              onClick={(e) => e.stopPropagation()}
              className="relative w-full max-w-md h-full bg-noir-900 border-l border-noir-800 overflow-y-auto"
            >
              <div className="p-6 space-y-6">
                {/* Header */}
                <div>
                  <div className={`inline-flex items-center gap-2 px-3 py-1 border text-sm font-mono mb-4 ${verdictStyles[data.verdict]}`}>
                    <div className={`w-1.5 h-1.5 ${verdictDot[data.verdict]}`} />
                    {data.verdict}
                  </div>
                  <h3 className="font-syne font-bold text-lg text-noir-50 mb-1">{criterionName}</h3>
                  <p className="text-sm text-noir-400 font-mono">{bidderName}</p>
                </div>

                {/* Extracted value */}
                <div className="border border-noir-800 p-4">
                  <span className="text-xs text-noir-500 font-mono block mb-2">EXTRACTED VALUE</span>
                  <p className="text-lg text-noir-100 font-newsreader">{data.extractedValue}</p>
                  <div className="flex items-center gap-4 mt-3">
                    <span className="text-xs text-noir-500 font-mono">
                      Method: <span className="text-noir-300">{data.method}</span>
                    </span>
                    <span className="text-xs text-noir-500 font-mono">
                      Page: <span className="text-noir-300">{data.sourcePage}</span>
                    </span>
                  </div>
                </div>

                {/* Confidence breakdown */}
                <div>
                  <span className="text-xs text-noir-500 font-mono block mb-3">CONFIDENCE BREAKDOWN</span>
                  <ConfidenceBar
                    extraction={data.signals.extraction}
                    ocr={data.signals.ocr}
                    retrieval={data.signals.retrieval}
                    llm={data.signals.llm}
                  />
                </div>

                {/* Explanation */}
                <div className="border border-noir-800 p-4">
                  <span className="text-xs text-noir-500 font-mono block mb-2">EXPLANATION</span>
                  <p className="text-sm text-noir-200 font-newsreader leading-relaxed">
                    {data.explanation}
                  </p>
                </div>

                <button
                  onClick={() => setShowDetail(false)}
                  className="w-full py-2.5 border border-noir-700 text-noir-300 text-sm font-mono hover:border-noir-500 hover:text-noir-100 transition-colors"
                >
                  CLOSE
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
