import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { FileText, AlertTriangle, Users, TrendingUp, ArrowRight, Loader2 } from 'lucide-react'
import StatsCard from '../components/StatsCard'
import { statusConfig } from '../data/tendersData'
import { getTenders, getDashboardStats } from '../api'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
}

export default function Dashboard() {
  const [tenders, setTenders] = useState([])
  const [stats, setStats] = useState({ active_tenders: 0, pending_reviews: 0, bidders_evaluated: 0, compliance_rate: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const [tendersRes, statsRes] = await Promise.all([
          getTenders(),
          getDashboardStats(),
        ])
        setTenders(tendersRes.tenders || [])
        setStats(statsRes)
      } catch (err) {
        console.error('Dashboard load error:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="pt-32 pb-16 px-6 lg:px-8 max-w-7xl mx-auto flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-6 h-6 text-amber-500 animate-spin" />
      </div>
    )
  }

  return (
    <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" className="pt-32 pb-16 px-6 lg:px-8 max-w-7xl mx-auto">

      {/* Header */}
      <div className="mb-10">
        <span className="text-sm font-mono text-amber-500 tracking-[0.4em] block mb-4">DASHBOARD</span>
        <h1 className="font-syne font-bold text-4xl md:text-5xl text-noir-50 tracking-tight">
          Tender Management
        </h1>
        <p className="text-noir-400 font-newsreader mt-3">
          Manage tender evaluations, upload bids, and review results
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="border border-crimson-700/30 bg-crimson-900/10 p-4 mb-6 text-sm text-crimson-400 font-mono">
          Failed to load: {error}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-px bg-noir-800/50 mb-10">
        <StatsCard value={stats.active_tenders} label="Active Tenders" icon={<FileText className="w-5 h-5" />} />
        <StatsCard value={stats.pending_reviews} label="Pending Reviews" icon={<AlertTriangle className="w-5 h-5" />} />
        <StatsCard value={stats.bidders_evaluated} label="Bidders Evaluated" icon={<Users className="w-5 h-5" />} />
        <StatsCard value={stats.compliance_rate} suffix="%" label="Compliance Rate" icon={<TrendingUp className="w-5 h-5" />} />
      </div>

      {/* Tenders List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-syne font-semibold text-xl text-noir-50">All Tenders</h2>
          <Link
            to="/tender/new"
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-noir-950 text-xs font-mono font-bold hover:bg-amber-400 transition-colors"
          >
            <FileText className="w-3.5 h-3.5" />
            NEW TENDER
          </Link>
        </div>

        {tenders.length === 0 && (
          <div className="border border-noir-800 bg-noir-900/40 p-12 text-center">
            <FileText className="w-8 h-8 text-noir-600 mx-auto mb-3" />
            <p className="text-noir-400 font-newsreader mb-2">No tenders yet</p>
            <Link to="/tender/new" className="text-amber-500 font-mono text-sm hover:text-amber-400">
              Create your first tender →
            </Link>
          </div>
        )}

        {tenders.map((tender, i) => (
          <motion.div
            key={tender.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Link
              to={`/tender/${tender.id}`}
              className="block border border-noir-800 bg-noir-900/60 hover:border-noir-700 hover:bg-noir-900/80 transition-all group"
            >
              <div className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-xs font-mono text-amber-500">{tender.id.slice(0, 8)}...</span>
                      {statusConfig[tender.status] && (
                        <span className={`text-xs font-mono px-2 py-0.5 border ${statusConfig[tender.status].color}`}>
                          {statusConfig[tender.status].label}
                        </span>
                      )}
                    </div>
                    <h3 className="font-syne font-bold text-xl text-noir-50 mb-1 group-hover:text-amber-400 transition-colors">
                      {tender.title}
                    </h3>
                    <p className="text-sm text-noir-400 font-newsreader">{tender.department}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-noir-600 group-hover:text-amber-500 group-hover:translate-x-1 transition-all shrink-0 mt-1" />
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 pt-4 border-t border-noir-800">
                  <div>
                    <span className="text-xs text-noir-500 font-mono block mb-1">VALUE</span>
                    <span className="text-sm font-syne font-semibold text-noir-200">{tender.estimated_value || '—'}</span>
                  </div>
                  <div>
                    <span className="text-xs text-noir-500 font-mono block mb-1">CRITERIA</span>
                    <span className="text-sm font-syne font-semibold text-noir-200">{tender.extracted_criteria_count || 0}</span>
                  </div>
                  <div>
                    <span className="text-xs text-noir-500 font-mono block mb-1">BIDDERS</span>
                    <span className="text-sm font-syne font-semibold text-noir-200">{tender.bidders_count || 0}</span>
                  </div>
                  <div>
                    <span className="text-xs text-noir-500 font-mono block mb-1">REVIEWS</span>
                    <span className={`text-sm font-syne font-semibold ${(tender.pending_reviews || 0) > 0 ? 'text-amber-400' : 'text-noir-200'}`}>
                      {tender.pending_reviews || 0}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-noir-500 font-mono block mb-1">PAGES</span>
                    <span className="text-sm font-mono text-noir-400">{tender.total_pages || '—'}</span>
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}
