import { useState } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, Filter } from 'lucide-react'
import ReviewItem from '../components/ReviewItem'
import { reviewItems } from '../data/mockData'

export default function ReviewQueue({ tenderId }) {
  const [items, setItems] = useState(reviewItems)
  const [filter, setFilter] = useState('all')
  const [actionLog, setActionLog] = useState([])

  const filtered = filter === 'all' ? items : items.filter((i) => i.urgency === filter)

  const handleConfirm = (id) => {
    setActionLog((prev) => [...prev, { id, action: 'CONFIRMED', time: new Date().toLocaleTimeString() }])
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  const handleOverride = (id) => {
    setActionLog((prev) => [...prev, { id, action: 'OVERRIDDEN', time: new Date().toLocaleTimeString() }])
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  const handleRescan = (id) => {
    setActionLog((prev) => [...prev, { id, action: 'RE-SCAN REQUESTED', time: new Date().toLocaleTimeString() }])
  }

  return (
    <div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-3">HUMAN IN THE LOOP</span>
          <h2 className="font-syne font-bold text-2xl md:text-3xl text-noir-50 tracking-tight mb-2">
            Review Queue
          </h2>
          <p className="text-noir-400 font-newsreader">
            Items below 90% confidence requiring officer judgement.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-noir-400">
            <Filter className="w-4 h-4" />
            <span className="text-xs font-mono">FILTER:</span>
          </div>
          <div className="flex gap-1">
            {['all', 'high', 'medium', 'low'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 text-xs font-mono transition-colors ${
                  filter === f
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    : 'text-noir-400 border border-transparent hover:text-noir-200'
                }`}
              >
                {f.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Pending count */}
      <div className="flex items-center gap-4 mb-8 p-5 border border-amber-700/30 bg-amber-900/10">
        <AlertTriangle className="w-5 h-5 text-amber-500" />
        <span className="text-base text-noir-200 font-newsreader">
          <strong className="text-amber-400 font-syne">{items.length}</strong> items pending review
        </span>
      </div>

      {/* Review items */}
      <div className="space-y-4">
        {filtered.length === 0 ? (
          <div className="text-center py-16 border border-noir-800 bg-noir-900/40">
            <p className="text-noir-400 font-newsreader">No items match the current filter.</p>
          </div>
        ) : (
          filtered.map((item) => (
            <ReviewItem
              key={item.id}
              item={item}
              onConfirm={handleConfirm}
              onOverride={handleOverride}
              onRescan={handleRescan}
            />
          ))
        )}
      </div>

      {/* Action log */}
      {actionLog.length > 0 && (
        <div className="mt-8 border border-noir-800 bg-noir-900/40">
          <div className="p-4 border-b border-noir-800">
            <h3 className="font-syne font-semibold text-noir-50 text-sm">SESSION LOG</h3>
          </div>
          <div className="p-4 space-y-2">
            {actionLog.map((log, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-xs font-mono text-noir-500">{log.time}</span>
                <span className="text-noir-300 font-newsreader">
                  Item {log.id} → <strong className="text-noir-100">{log.action}</strong>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
