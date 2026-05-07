import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, Filter, Loader2 } from 'lucide-react'
import ReviewItem from '../components/ReviewItem'
import { getReviewQueue, request } from '../api'

export default function ReviewQueue({ tenderId }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  const fetchReviewQueue = async () => {
    setLoading(true)
    try {
      const data = await getReviewQueue(tenderId)
      setItems(data.items || [])
    } catch (error) {
      console.error('Error fetching review queue:', error)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (tenderId) {
      fetchReviewQueue()
    }
  }, [tenderId])

  const filteredItems = items.filter(item => {
    if (filter === 'all') return true
    if (filter === 'pending') return item.status === 'pending'
    return item.urgency === filter
  })

  const urgencyCounts = {
    high: items.filter(i => i.urgency === 'high' && i.status === 'pending').length,
    medium: items.filter(i => i.urgency === 'medium' && i.status === 'pending').length,
    low: items.filter(i => i.urgency === 'low' && i.status === 'pending').length,
  }

  const handleConfirm = async (id) => {
    try {
      await request(`/review-queue/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          status: 'confirmed',
          officer: 'System User',
          reason: 'Confirmed as PASS by officer'
        })
      })
      // Refresh after action
      fetchReviewQueue()
    } catch (error) {
      console.error('Error confirming review item:', error)
      alert('Failed to confirm item')
    }
  }

  const handleOverride = async (id) => {
    try {
      await request(`/review-queue/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          status: 'overridden',
          officer: 'System User',
          reason: 'Marked as FAIL by officer'
        })
      })
      // Refresh after action
      fetchReviewQueue()
    } catch (error) {
      console.error('Error overriding review item:', error)
      alert('Failed to override item')
    }
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

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="border border-crimson-600/30 bg-crimson-900/10 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-crimson-400" />
            <span className="text-xs font-mono text-crimson-400">HIGH URGENCY</span>
          </div>
          <div className="text-2xl font-syne font-bold text-crimson-300">{urgencyCounts.high}</div>
        </div>
        <div className="border border-amber-700/30 bg-amber-900/10 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="text-xs font-mono text-amber-500">MEDIUM URGENCY</span>
          </div>
          <div className="text-2xl font-syne font-bold text-amber-400">{urgencyCounts.medium}</div>
        </div>
        <div className="border border-noir-700 bg-noir-800/40 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-noir-400" />
            <span className="text-xs font-mono text-noir-400">LOW URGENCY</span>
          </div>
          <div className="text-2xl font-syne font-bold text-noir-300">{urgencyCounts.low}</div>
        </div>
      </div>

      {/* Review items */}
      {loading ? (
        <div className="flex items-center justify-center p-12 border border-noir-800 bg-noir-900/30">
          <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="text-center py-16 border border-noir-800 bg-noir-900/40">
          <AlertTriangle className="w-12 h-12 text-noir-600 mx-auto mb-4" />
          <p className="text-noir-400 font-newsreader">No items in review queue.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <ReviewItem
                item={item}
                onConfirm={handleConfirm}
                onOverride={handleOverride}
              />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
