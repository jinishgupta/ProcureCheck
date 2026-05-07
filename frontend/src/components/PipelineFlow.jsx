import { motion } from 'framer-motion'
import { FileText, Search, CheckCircle } from 'lucide-react'

const stages = [
  {
    number: '01',
    title: 'Tender Ingestion',
    subtitle: 'Parse · Infer · Extract',
    icon: <FileText className="w-5 h-5" />,
    details: [
      'Native PDF parsing via PyMuPDF',
      'Scanned pages → Google Cloud Vision',
      'Automatic criterion type inference',
      'Llama 3.3 extraction via Groq',
      'Structured requirement mapping',
    ],
  },
  {
    number: '02',
    title: 'Bidder Pipeline',
    subtitle: 'OCR · Index · Vectorize',
    icon: <Search className="w-5 h-5" />,
    details: [
      'Parallel processing via ThreadPool',
      'FAISS vector index (Per-Bidder)',
      'all-MiniLM-L6-v2 embeddings',
      'Per-page OCR confidence scoring',
      'Isolated document fingerprinting',
    ],
  },
  {
    number: '03',
    title: 'AI Matching Engine',
    subtitle: 'Retrieve · Evaluate · Score',
    icon: <CheckCircle className="w-5 h-5" />,
    details: [
      'Top-3 relevant evidence retrieval',
      'Hybrid Extraction: Regex + Llama',
      'Weighted 4-Signal confidence logic',
      'Pass/Fail/Review verdict generation',
      'Immutable Audit Trail recording',
    ],
  },
]

export default function PipelineFlow() {
  return (
    <div className="relative">
      {/* Connecting line - positioned at the top of the cards */}
      <div className="hidden lg:block absolute top-[120px] left-0 right-0 h-px bg-noir-800" />
      <motion.div
        className="hidden lg:block absolute top-[120px] left-0 h-px bg-amber-500/40"
        initial={{ width: '0%' }}
        whileInView={{ width: '100%' }}
        viewport={{ once: true }}
        transition={{ duration: 1.8, ease: 'easeInOut', delay: 0.3 }}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        {stages.map((stage, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 + i * 0.2 }}
            className="relative group flex"
          >
            {/* Node dot on the line */}
            <div className="hidden lg:flex absolute top-[120px] left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 border-2 border-amber-500 bg-noir-950 z-10 items-center justify-center rounded-full">
              <div className="w-2 h-2 bg-amber-500 rounded-full" />
            </div>

            <div className="lg:pt-[140px] w-full flex">
              <div className="border border-noir-800 bg-noir-900/80 p-6 lg:p-8 hover:border-noir-700 transition-all duration-500 w-full flex flex-col">
                {/* Stage number */}
                <div className="flex items-center gap-3 mb-4">
                  <span className="font-mono text-xs text-amber-500 tracking-widest">
                    STAGE {stage.number}
                  </span>
                  <div className="flex-1 h-px bg-noir-800" />
                  <div className="text-amber-500/60">{stage.icon}</div>
                </div>

                <h3 className="font-syne font-bold text-xl lg:text-2xl text-noir-50 mb-2 tracking-tight">
                  {stage.title}
                </h3>
                <p className="text-sm lg:text-base text-noir-400 font-mono tracking-wide mb-6">
                  {stage.subtitle}
                </p>

                <ul className="space-y-2.5 flex-1">
                  {stage.details.map((detail, j) => (
                    <li key={j} className="flex items-start gap-2 text-sm lg:text-base text-noir-300">
                      <span className="text-amber-500/50 mt-1 shrink-0">›</span>
                      <span className="font-newsreader leading-relaxed">{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
