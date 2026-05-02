import { useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, Download, Search, Hash, User, Clock, FileText } from 'lucide-react'
import { auditLogs } from '../data/mockData'

const actionColors = {
  TENDER_UPLOADED: 'text-jade-400',
  OCR_COMPLETED: 'text-jade-400',
  CRITERIA_EXTRACTED: 'text-jade-400',
  CORRIGENDUM_APPLIED: 'text-amber-400',
  BIDDER_UPLOADED: 'text-noir-300',
  EVALUATION_STARTED: 'text-amber-500',
  EVALUATION_COMPLETE: 'text-jade-400',
  REVIEW_CONFIRMED: 'text-crimson-400',
  REVIEW_OVERRIDE: 'text-amber-400',
  REPORT_EXPORTED: 'text-noir-200',
}

export default function AuditTrail({ tenderId }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterAction, setFilterAction] = useState('all')

  const actions = ['all', ...new Set(auditLogs.map((l) => l.action))]

  const filtered = auditLogs.filter((log) => {
    const matchesSearch = searchQuery === '' || log.detail.toLowerCase().includes(searchQuery.toLowerCase()) || log.officer.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesAction = filterAction === 'all' || log.action === filterAction
    return matchesSearch && matchesAction
  })

  return (
    <div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-3">COMPLIANCE</span>
          <h2 className="font-syne font-bold text-2xl md:text-3xl text-noir-50 tracking-tight mb-2">
            Audit Trail
          </h2>
          <p className="text-noir-400 font-newsreader">
            Immutable log of every system and officer action.
          </p>
        </div>

        <button className="flex items-center gap-2 px-5 py-2.5 bg-amber-500 text-noir-950 text-xs font-mono font-semibold hover:bg-amber-400 transition-colors self-start">
          <Download className="w-3.5 h-3.5" />
          EXPORT PDF REPORT
        </button>
      </div>

      {/* Search & filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-noir-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search logs..."
            className="w-full bg-noir-900 border border-noir-800 pl-10 pr-4 py-2.5 text-sm text-noir-200 font-mono placeholder:text-noir-600 focus:outline-none focus:border-noir-600 transition-colors"
          />
        </div>
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          className="bg-noir-900 border border-noir-800 px-4 py-2.5 text-sm text-noir-200 font-mono focus:outline-none focus:border-noir-600 transition-colors appearance-none cursor-pointer"
        >
          {actions.map((a) => (
            <option key={a} value={a} className="bg-noir-900">
              {a === 'all' ? 'ALL ACTIONS' : a}
            </option>
          ))}
        </select>
      </div>

      {/* Integrity banner */}
      <div className="flex items-center gap-4 mb-8 p-5 border border-jade-700/30 bg-jade-900/10">
        <Shield className="w-5 h-5 text-jade-500" />
        <span className="text-base text-noir-200 font-newsreader">
          All entries are immutable. SHA-256 document fingerprints ensure tamper detection.
        </span>
      </div>

      {/* Log entries */}
      <div className="border border-noir-800 bg-noir-900/30">
        <div className="divide-y divide-noir-800/50">
          {filtered.map((log, i) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.03 }}
              className="p-4 hover:bg-noir-800/20 transition-colors"
            >
              <div className="flex flex-col md:flex-row md:items-start gap-3">
                {/* Timestamp */}
                <div className="flex items-center gap-2 shrink-0 w-44">
                  <Clock className="w-3.5 h-3.5 text-noir-600" />
                  <span className="text-xs font-mono text-noir-400">{log.timestamp}</span>
                </div>

                {/* Action badge */}
                <div className="shrink-0">
                  <span className={`text-xs font-mono px-2 py-0.5 border border-noir-700 ${actionColors[log.action] || 'text-noir-300'}`}>
                    {log.action}
                  </span>
                </div>

                {/* Detail */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-noir-200 font-newsreader mb-1">{log.detail}</p>
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-1.5">
                      <User className="w-3 h-3 text-noir-600" />
                      <span className="text-xs font-mono text-noir-500">{log.officer}</span>
                    </div>
                    {log.docHash && (
                      <div className="flex items-center gap-1.5">
                        <Hash className="w-3 h-3 text-noir-600" />
                        <span className="text-xs font-mono text-noir-500">{log.docHash}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1.5">
                      <FileText className="w-3 h-3 text-noir-600" />
                      <span className="text-xs font-mono text-noir-500">v{log.version}</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Entry count */}
      <div className="mt-4 text-xs text-noir-500 font-mono text-right">
        Showing {filtered.length} of {auditLogs.length} entries
      </div>
    </div>
  )
}
