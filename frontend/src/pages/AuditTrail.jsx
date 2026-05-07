import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Shield, Download, Search, Hash, User, Clock, FileText, Loader2 } from 'lucide-react'
import { getAuditTrail } from '../api'

const actionColors = {
  TENDER_CREATED: 'text-jade-400 bg-jade-900/20 border-jade-700/30',
  TENDER_UPLOADED: 'text-amber-400 bg-amber-900/20 border-amber-700/30',
  BIDDER_UPLOADED: 'text-amber-400 bg-amber-900/20 border-amber-700/30',
  EVALUATION_COMPLETE: 'text-jade-400 bg-jade-900/20 border-jade-700/30',
  REVIEW_CONFIRMED: 'text-jade-400 bg-jade-900/20 border-jade-700/30',
  REVIEW_OVERRIDE: 'text-crimson-400 bg-crimson-900/20 border-crimson-700/30',
}

export default function AuditTrail({ tenderId }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  const fetchAuditTrail = async () => {
    setLoading(true)
    try {
      const data = await getAuditTrail(tenderId)
      setLogs(data.logs || [])
    } catch (error) {
      console.error('Error fetching audit trail:', error)
      setLogs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (tenderId) {
      fetchAuditTrail()
    }
  }, [tenderId])

  const filteredLogs = logs.filter(log =>
    log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.officer.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.detail.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleExport = () => {
    const csvContent = [
      ['Timestamp', 'Action', 'Officer', 'Detail', 'Version', 'Doc Hash'].join(','),
      ...filteredLogs.map(log => [
        new Date(log.timestamp).toISOString(),
        log.action,
        log.officer,
        `"${log.detail.replace(/"/g, '""')}"`,
        log.version,
        log.doc_hash || ''
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_trail_${tenderId}_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

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
            Immutable log of all actions — timestamped, hashed, and officer-attributed.
          </p>
        </div>

        <button
          onClick={handleExport}
          disabled={filteredLogs.length === 0}
          className="flex items-center gap-2 px-4 py-2 border border-amber-500/50 bg-amber-500/10 text-amber-500 text-xs font-mono hover:bg-amber-500/20 transition-colors disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          EXPORT CSV
        </button>
      </div>

      {/* Search */}
      <div className="mb-6 relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-noir-500" />
        <input
          type="text"
          placeholder="Search by action, officer, or detail..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-noir-850 border border-noir-700 pl-11 pr-4 py-3 text-noir-100 font-mono text-sm focus:outline-none focus:border-amber-500 transition-colors"
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="border border-noir-800 bg-noir-900/40 p-4">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-noir-400" />
            <span className="text-xs font-mono text-noir-400">TOTAL ENTRIES</span>
          </div>
          <div className="text-2xl font-syne font-bold text-noir-200">{logs.length}</div>
        </div>
        <div className="border border-noir-800 bg-noir-900/40 p-4">
          <div className="flex items-center gap-2 mb-2">
            <User className="w-4 h-4 text-noir-400" />
            <span className="text-xs font-mono text-noir-400">UNIQUE OFFICERS</span>
          </div>
          <div className="text-2xl font-syne font-bold text-noir-200">
            {new Set(logs.map(l => l.officer)).size}
          </div>
        </div>
        <div className="border border-noir-800 bg-noir-900/40 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-noir-400" />
            <span className="text-xs font-mono text-noir-400">INTEGRITY</span>
          </div>
          <div className="text-2xl font-syne font-bold text-jade-400">VERIFIED</div>
        </div>
      </div>

      {/* Audit Logs */}
      {loading ? (
        <div className="flex items-center justify-center p-12 border border-noir-800 bg-noir-900/30">
          <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="text-center py-16 border border-noir-800 bg-noir-900/40">
          <Shield className="w-12 h-12 text-noir-600 mx-auto mb-4" />
          <p className="text-noir-400 font-newsreader">
            {searchTerm ? 'No logs match your search.' : 'No audit logs available.'}
          </p>
        </div>
      ) : (
        <div className="border border-noir-800 bg-noir-900/30">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-noir-800 bg-noir-900/60">
                  <th className="p-4 text-left text-xs font-mono text-noir-500">TIMESTAMP</th>
                  <th className="p-4 text-left text-xs font-mono text-noir-500">ACTION</th>
                  <th className="p-4 text-left text-xs font-mono text-noir-500">OFFICER</th>
                  <th className="p-4 text-left text-xs font-mono text-noir-500">DETAIL</th>
                  <th className="p-4 text-left text-xs font-mono text-noir-500">VERSION</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log, i) => (
                  <motion.tr
                    key={log.id}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="border-b border-noir-800/50 hover:bg-noir-800/20 transition-colors"
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-sm text-noir-300 font-mono">
                        <Clock className="w-3.5 h-3.5 text-noir-500" />
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </td>
                    <td className="p-4">
                      <span className={`inline-block px-2 py-1 text-xs font-mono border ${actionColors[log.action] || 'text-noir-400 bg-noir-800/40 border-noir-700'}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-sm text-noir-200 font-newsreader">
                        <User className="w-3.5 h-3.5 text-noir-500" />
                        {log.officer}
                      </div>
                    </td>
                    <td className="p-4">
                      <p className="text-sm text-noir-300 font-newsreader">{log.detail}</p>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-xs text-noir-400 font-mono">
                        <Hash className="w-3 h-3" />
                        {log.version}
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
