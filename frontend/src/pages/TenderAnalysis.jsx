import { useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, AlertTriangle, Loader2, ScanLine } from 'lucide-react'
import FileUpload from '../components/FileUpload'
import CriterionCard from '../components/CriterionCard'
import { extractedCriteria } from '../data/mockData'

const processingSteps = [
  { label: 'Page Classification', detail: 'Native vs Scanned detection', status: 'done' },
  { label: 'OCR Processing', detail: '144 scanned pages via Cloud Vision', status: 'done' },
  { label: 'Section Detection', detail: 'Heading heuristics + clause regex', status: 'done' },
  { label: 'Criteria Extraction', detail: 'Two-stage LLM (Flash → Pro)', status: 'done' },
  { label: 'Cross-Reference Resolution', detail: 'Gap-fill LLM calls', status: 'done' },
]

export default function TenderAnalysis({ tenderId }) {
  const [showResults, setShowResults] = useState(true)
  const [filterType, setFilterType] = useState('all')

  const filteredCriteria = filterType === 'all'
    ? extractedCriteria
    : extractedCriteria.filter((c) => c.type === filterType)

  const types = ['all', 'financial', 'technical', 'certification', 'experience']

  return (
    <div>

      {/* Header */}
      <div className="mb-8">
        <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-3">STAGE 1</span>
        <h2 className="font-syne font-bold text-2xl md:text-3xl text-noir-50 tracking-tight mb-2">
          Tender Analysis
        </h2>
        <p className="text-noir-400 font-newsreader">
          Upload a tender document to extract eligibility criteria automatically.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

        {/* Left: Upload + Processing */}
        <div className="space-y-6">
          <FileUpload onFilesSelected={() => {}} />

          {/* Processing Steps */}
          <div className="border border-noir-800 bg-noir-900/60">
            <div className="p-6 border-b border-noir-800">
              <h3 className="font-syne font-bold text-noir-50 text-base tracking-wide">PROCESSING PIPELINE</h3>
            </div>
            <div className="p-6 space-y-4">
              {processingSteps.map((step, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-3"
                >
                  <div className="mt-0.5 shrink-0">
                    {step.status === 'done' ? (
                      <CheckCircle2 className="w-4 h-4 text-jade-500" />
                    ) : step.status === 'active' ? (
                      <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />
                    ) : (
                      <div className="w-4 h-4 border border-noir-700" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-noir-200 font-newsreader">{step.label}</p>
                    <p className="text-xs text-noir-500 font-mono">{step.detail}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Extracted Criteria */}
        <div className="lg:col-span-3">
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
            <div className="divide-y divide-noir-800/30">
              {filteredCriteria.map((criterion, i) => (
                <CriterionCard key={criterion.id} criterion={criterion} index={i} />
              ))}
            </div>

            {/* Summary bar */}
            <div className="p-6 border-t border-noir-800 flex flex-wrap gap-6">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-amber-500" />
                <span className="text-xs text-noir-400 font-mono">
                  {extractedCriteria.filter((c) => c.mandatory).length} Mandatory
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-noir-500" />
                <span className="text-xs text-noir-400 font-mono">
                  {extractedCriteria.filter((c) => !c.mandatory).length} Optional
                </span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-3 h-3 text-amber-500" />
                <span className="text-xs text-noir-400 font-mono">
                  {extractedCriteria.filter((c) => c.unresolvedRef).length} Unresolved Refs
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
