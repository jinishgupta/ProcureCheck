import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, AlertTriangle, Loader2, ScanLine } from 'lucide-react'
import CriterionCard from '../components/CriterionCard'
import { getCriteria } from '../api'

export default function TenderAnalysis({ tenderId }) {
  const [criteria, setCriteria] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterType, setFilterType] = useState('all')

  useEffect(() => {
    async function load() {
      try {
        const res = await getCriteria(tenderId)
        setCriteria(res.criteria || [])
      } catch (err) {
        console.error('Failed to load criteria:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [tenderId])

  const filteredCriteria = filterType === 'all'
    ? criteria
    : criteria.filter((c) => c.type === filterType)

  const types = ['all', 'financial', 'technical', 'certification', 'experience']

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 text-amber-500 animate-spin" />
      </div>
    )
  }

  return (
    <div>

      {/* Header */}
      <div className="mb-8">
        <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-3">STAGE 1</span>
        <h2 className="font-syne font-bold text-2xl md:text-3xl text-noir-50 tracking-tight mb-2">
          Tender Analysis
        </h2>
        <p className="text-noir-400 font-newsreader">
          Extracted eligibility criteria from the tender document.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="border border-crimson-700/30 bg-crimson-900/10 p-4 mb-6 text-sm text-crimson-400 font-mono">
          Failed to load criteria: {error}
        </div>
      )}

      {/* Extracted Criteria */}
      <div className="border border-noir-800 bg-noir-900/40">
        {/* Header */}
        <div className="p-6 border-b border-noir-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <ScanLine className="w-5 h-5 text-amber-500" />
            <h3 className="font-syne font-bold text-noir-50 text-base tracking-wide">
              EXTRACTED CRITERIA
            </h3>
            <span className="text-sm font-mono text-noir-400 ml-2">{filteredCriteria.length} items</span>
          </div>

          {/* Filter tabs */}
          <div className="flex gap-1">
            {types.map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-3 py-1 text-xs font-mono transition-colors ${
                  filterType === type
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    : 'text-noir-400 border border-transparent hover:text-noir-200'
                }`}
              >
                {type.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Criteria list */}
        {filteredCriteria.length === 0 ? (
          <div className="p-12 text-center">
            <ScanLine className="w-8 h-8 text-noir-600 mx-auto mb-3" />
            <p className="text-noir-400 font-newsreader">
              {criteria.length === 0
                ? 'No criteria extracted yet. Upload a tender document to begin.'
                : 'No criteria match this filter.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-noir-800/30">
            {filteredCriteria.map((criterion, i) => (
              <CriterionCard
                key={criterion.id}
                criterion={{
                  ...criterion,
                  // Map snake_case to camelCase for the component
                  unresolvedRef: criterion.unresolved_ref,
                }}
                index={i}
              />
            ))}
          </div>
        )}

        {/* Summary bar */}
        {criteria.length > 0 && (
          <div className="p-6 border-t border-noir-800 flex flex-wrap gap-6">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-amber-500" />
              <span className="text-xs text-noir-400 font-mono">
                {criteria.filter((c) => c.mandatory).length} Mandatory
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-noir-500" />
              <span className="text-xs text-noir-400 font-mono">
                {criteria.filter((c) => !c.mandatory).length} Optional
              </span>
            </div>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3 h-3 text-amber-500" />
              <span className="text-xs text-noir-400 font-mono">
                {criteria.filter((c) => c.unresolved_ref).length} Unresolved Refs
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
