import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, FileText, Users, AlertTriangle, Activity, Loader2 } from 'lucide-react'
import { getTender } from '../api'
import TenderAnalysis from './TenderAnalysis'
import BidderMatrix from './BidderMatrix'
import ReviewQueue from './ReviewQueue'
import AuditTrail from './AuditTrail'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
}

const tabs = [
  { id: 'analysis', label: 'Tender Analysis', icon: <FileText className="w-4 h-4" /> },
  { id: 'bidders', label: 'Bidder Matrix', icon: <Users className="w-4 h-4" /> },
  { id: 'review', label: 'Review Queue', icon: <AlertTriangle className="w-4 h-4" /> },
  { id: 'audit', label: 'Audit Trail', icon: <Activity className="w-4 h-4" /> },
]

export default function TenderWorkspace() {
  const { tenderId } = useParams()
  const [activeTab, setActiveTab] = useState('analysis')
  const [tender, setTender] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const data = await getTender(tenderId)
        setTender(data)
      } catch (err) {
        console.error('Failed to load tender:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [tenderId])

  if (loading) {
    return (
      <div className="pt-32 pb-16 px-6 lg:px-8 max-w-7xl mx-auto flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-6 h-6 text-amber-500 animate-spin" />
      </div>
    )
  }

  if (error || !tender) {
    return (
      <div className="pt-32 pb-16 px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center">
          <h1 className="font-syne font-bold text-3xl text-noir-50 mb-4">
            {error ? 'Error Loading Tender' : 'Tender Not Found'}
          </h1>
          {error && <p className="text-crimson-400 font-mono text-sm mb-4">{error}</p>}
          <Link to="/dashboard" className="text-amber-500 hover:text-amber-400 font-mono text-sm">
                ← Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'analysis':
        return <TenderAnalysis tenderId={tenderId} />
      case 'bidders':
        return <BidderMatrix tenderId={tenderId} />
      case 'review':
        return <ReviewQueue tenderId={tenderId} />
      case 'audit':
        return <AuditTrail tenderId={tenderId} />
      default:
        return <TenderAnalysis tenderId={tenderId} />
    }
  }

  return (
    <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" className="pt-24 pb-16 px-6 lg:px-8 max-w-7xl mx-auto">
      
      {/* Back Button */}
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-2 text-noir-400 hover:text-amber-500 font-mono text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Tender Header */}
      <div className="mb-8 pb-6 border-b border-noir-800">
        <div className="flex items-start justify-between mb-4">
          <div>
            <span className="text-xs font-mono text-amber-500 block mb-2">{tender.id.slice(0, 8)}...</span>
            <h1 className="font-syne font-bold text-3xl md:text-4xl text-noir-50 tracking-tight mb-2">
              {tender.title}
            </h1>
            <p className="text-noir-400 font-newsreader">{tender.department}</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
          <div className="border border-noir-800 bg-noir-900/40 p-4">
            <span className="text-xs text-noir-500 font-mono block mb-1">VALUE</span>
            <span className="text-lg font-syne font-bold text-noir-100">{tender.estimated_value || '—'}</span>
          </div>
          <div className="border border-noir-800 bg-noir-900/40 p-4">
            <span className="text-xs text-noir-500 font-mono block mb-1">CRITERIA</span>
            <span className="text-lg font-syne font-bold text-noir-100">{tender.extracted_criteria_count || 0}</span>
          </div>
          <div className="border border-noir-800 bg-noir-900/40 p-4">
            <span className="text-xs text-noir-500 font-mono block mb-1">BIDDERS</span>
            <span className="text-lg font-syne font-bold text-noir-100">{tender.bidders_count || 0}</span>
          </div>
          <div className="border border-noir-800 bg-noir-900/40 p-4">
            <span className="text-xs text-noir-500 font-mono block mb-1">REVIEWS</span>
            <span className={`text-lg font-syne font-bold ${(tender.pending_reviews || 0) > 0 ? 'text-amber-400' : 'text-noir-100'}`}>
              {tender.pending_reviews || 0}
            </span>
          </div>
          <div className="border border-noir-800 bg-noir-900/40 p-4">
            <span className="text-xs text-noir-500 font-mono block mb-1">PAGES</span>
            <span className="text-lg font-syne font-bold text-noir-100">{tender.total_pages || '—'}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-noir-800 mb-8">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 font-mono text-sm transition-all relative ${
                activeTab === tab.id
                  ? 'text-amber-400 bg-noir-900/60'
                  : 'text-noir-400 hover:text-noir-200 hover:bg-noir-900/30'
              }`}
            >
              {tab.icon}
              {tab.label}
              {activeTab === tab.id && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-500"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {renderTabContent()}
      </div>
    </motion.div>
  )
}
