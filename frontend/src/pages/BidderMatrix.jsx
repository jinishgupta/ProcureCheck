import { motion } from 'framer-motion'
import { Users, AlertTriangle } from 'lucide-react'
import MatrixCell from '../components/MatrixCell'
import { bidders, extractedCriteria, matrixData } from '../data/mockData'

// Use a subset of criteria that have matrix data
const matrixCriteria = extractedCriteria.filter((c) => [1, 2, 3, 8, 9].includes(c.id))

export default function BidderMatrix({ tenderId }) {
  // Count verdicts
  const verdictCounts = { PASS: 0, FAIL: 0, REVIEW: 0 }
  Object.values(matrixData).forEach((bidder) => {
    Object.values(bidder).forEach((cell) => {
      verdictCounts[cell.verdict]++
    })
  })

  return (
    <div>

      {/* Header */}
      <div className="mb-8">
        <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-3">STAGE 3</span>
        <h2 className="font-syne font-bold text-2xl md:text-3xl text-noir-50 tracking-tight mb-2">
          Bidder Comparison Matrix
        </h2>
        <p className="text-noir-400 font-newsreader">
          Color-coded evaluation grid — click any cell for full confidence breakdown.
        </p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-8 mb-8 p-6 border border-noir-800 bg-noir-900/40">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-jade-900/60 border border-jade-700/40" />
          <span className="text-xs font-mono text-noir-300">PASS ({verdictCounts.PASS})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-crimson-900/60 border border-crimson-600/40" />
          <span className="text-xs font-mono text-noir-300">FAIL ({verdictCounts.FAIL})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-amber-900/40 border border-amber-700/40" />
          <span className="text-xs font-mono text-noir-300">REVIEW ({verdictCounts.REVIEW})</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Users className="w-4 h-4 text-noir-500" />
          <span className="text-xs font-mono text-noir-400">{bidders.length} Bidders × {matrixCriteria.length} Criteria</span>
        </div>
      </div>

      {/* Matrix Table */}
      <div className="border border-noir-800 bg-noir-900/30 overflow-x-auto">
        <table className="w-full min-w-[700px]">
          <thead>
            <tr className="border-b border-noir-800">
              <th className="p-4 text-left text-xs font-mono text-noir-500 w-48 bg-noir-900/80 sticky left-0 z-10">
                CRITERION
              </th>
              {bidders.map((bidder) => (
                <th key={bidder.id} className="p-4 text-center">
                  <div className="text-xs font-syne font-semibold text-noir-100 mb-0.5">{bidder.name}</div>
                  <div className="text-xs font-mono text-noir-500">{bidder.location}</div>
                  <div className="flex items-center justify-center gap-1 mt-1">
                    <div className={`w-1.5 h-1.5 ${bidder.ocrConfidence >= 0.9 ? 'bg-jade-500' : bidder.ocrConfidence >= 0.8 ? 'bg-amber-500' : 'bg-crimson-500'}`} />
                    <span className="text-xs font-mono text-noir-500">OCR {(bidder.ocrConfidence * 100).toFixed(0)}%</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrixCriteria.map((criterion) => (
              <tr key={criterion.id} className="border-b border-noir-800/50 hover:bg-noir-800/10 transition-colors">
                <td className="p-4 bg-noir-900/80 sticky left-0 z-10 border-r border-noir-800/50">
                  <div className="text-sm text-noir-200 font-newsreader mb-0.5">{criterion.field}</div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-noir-500">{criterion.type}</span>
                    {criterion.mandatory && <span className="text-xs font-mono text-amber-500">M</span>}
                  </div>
                </td>
                {bidders.map((bidder) => {
                  const cellData = matrixData[bidder.id]?.[criterion.id]
                  if (!cellData) {
                    return (
                      <td key={bidder.id} className="p-2">
                        <div className="flex items-center justify-center aspect-square border border-noir-800 bg-noir-900/40 text-noir-600 text-xs font-mono">
                          N/A
                        </div>
                      </td>
                    )
                  }
                  return (
                    <td key={bidder.id} className="p-2">
                      <MatrixCell
                        data={cellData}
                        bidderName={bidder.name}
                        criterionName={criterion.field}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Cross-validation alerts */}
      <div className="mt-6 space-y-2">
        <h3 className="font-syne font-semibold text-noir-50 text-sm mb-3">CROSS-DOCUMENT ALERTS</h3>
        {[
          { bidder: 'Surya Protective Gear', issue: 'Company name inconsistency between PAN card ("Surya Protective Gear Pvt Ltd") and work orders ("Surya Protection Systems")', severity: 'high' },
          { bidder: 'ShieldTech Industries', issue: 'Turnover value in balance sheet (₹14.8Cr) differs from ITR summary (₹15.1Cr) — variance 2.0%', severity: 'medium' },
        ].map((alert, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`flex items-start gap-3 p-4 border ${
              alert.severity === 'high' ? 'border-crimson-600/30 bg-crimson-900/10' : 'border-amber-700/30 bg-amber-900/10'
            }`}
          >
            <AlertTriangle className={`w-4 h-4 shrink-0 mt-0.5 ${alert.severity === 'high' ? 'text-crimson-400' : 'text-amber-500'}`} />
            <div>
              <span className="text-xs font-mono text-noir-400 block mb-0.5">{alert.bidder}</span>
              <p className="text-sm text-noir-200 font-newsreader">{alert.issue}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
