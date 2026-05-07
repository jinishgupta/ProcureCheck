import { useState } from 'react'
import { motion } from 'framer-motion'
import { Users, AlertTriangle, Download, Plus } from 'lucide-react'
import MatrixCell from '../components/MatrixCell'
import { bidders, extractedCriteria, matrixData } from '../data/mockData'
import BidderUploadModal from '../components/BidderUploadModal'
import jsPDF from 'jspdf'
import 'jspdf-autotable'

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

  const [showUpload, setShowUpload] = useState(false)

  const handleExportPDF = () => {
    const doc = new jsPDF()
    
    // Header
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(20)
    doc.text('Tender Evaluation Report', 14, 22)
    
    doc.setFontSize(12)
    doc.setFont('helvetica', 'normal')
    doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 14, 30)
    
    // Summary
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(14)
    doc.text('Executive Summary', 14, 45)
    
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    const summaryText = `This report evaluates ${bidders.length} bidders against ${matrixCriteria.length} key eligibility criteria. Below is the detailed breakdown of selections, rejections, and items flagged for manual review.`
    doc.text(doc.splitTextToSize(summaryText, 180), 14, 52)
    
    let currentY = 70
    
    bidders.forEach((bidder, index) => {
      if (currentY > 250) {
        doc.addPage()
        currentY = 20
      }
      
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(12)
      doc.text(`${index + 1}. ${bidder.name}`, 14, currentY)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(10)
      doc.text(`Location: ${bidder.location} | Overall OCR Confidence: ${(bidder.ocrConfidence * 100).toFixed(0)}%`, 14, currentY + 6)
      
      currentY += 15
      
      const tableData = []
      let passCount = 0
      let failCount = 0
      let reviewCount = 0
      
      matrixCriteria.forEach(crit => {
        const cell = matrixData[bidder.id]?.[crit.id]
        if (cell) {
          if (cell.verdict === 'PASS') passCount++
          if (cell.verdict === 'FAIL') failCount++
          if (cell.verdict === 'REVIEW') reviewCount++
          
          tableData.push([
            crit.field,
            cell.verdict,
            cell.extractedValue,
            cell.explanation
          ])
        }
      })
      
      let status = 'SELECTED'
      if (failCount > 0) status = 'REJECTED'
      else if (reviewCount > 0) status = 'MARKED FOR REVIEW'
      
      doc.setFont('helvetica', 'bold')
      doc.text(`Overall Status: ${status}`, 14, currentY)
      currentY += 8
      
      let text = ""
      if (status === 'SELECTED') {
        text = `Bidder passed all ${passCount} criteria with high confidence. Recommended for next stage.`
      } else if (status === 'REJECTED') {
        text = `Bidder failed ${failCount} criteria and cannot proceed.`
      } else {
        text = `Bidder passed ${passCount} criteria but requires manual verification on ${reviewCount} criteria.`
      }
      doc.setFont('helvetica', 'italic')
      doc.text(text, 14, currentY)
      currentY += 8
      
      doc.autoTable({
        startY: currentY,
        head: [['Criterion', 'Verdict', 'Extracted Value', 'Explanation']],
        body: tableData,
        theme: 'grid',
        headStyles: { fillColor: [40, 40, 40] },
        styles: { fontSize: 8, cellPadding: 3 },
        columnStyles: {
          0: { cellWidth: 35 },
          1: { cellWidth: 20 },
          2: { cellWidth: 35 },
          3: { cellWidth: 'auto' }
        }
      })
      
      currentY = doc.lastAutoTable.finalY + 20
    })
    
    doc.save('Tender_Evaluation_Report.pdf')
  }

  return (
    <div>

      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-3">STAGE 3</span>
          <h2 className="font-syne font-bold text-2xl md:text-3xl text-noir-50 tracking-tight mb-2">
            Bidder Comparison Matrix
          </h2>
          <p className="text-noir-400 font-newsreader">
            Color-coded evaluation grid — click any cell for full confidence breakdown.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-4 py-2 border border-noir-700 bg-noir-800 text-noir-200 text-xs font-mono hover:bg-noir-700 hover:text-noir-50 transition-colors"
          >
            <Plus className="w-4 h-4" />
            ADD BIDDER
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-2 px-4 py-2 border border-amber-500/50 bg-amber-500/10 text-amber-500 text-xs font-mono hover:bg-amber-500/20 transition-colors"
          >
            <Download className="w-4 h-4" />
            EXPORT REPORT
          </button>
        </div>
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

      {showUpload && (
        <BidderUploadModal
          tenderId={tenderId}
          onClose={() => setShowUpload(false)}
          onSuccess={() => {
            // UI refresh logic here
          }}
        />
      )}
    </div>
  )
}
