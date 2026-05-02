import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Shield, ScanLine, Brain, Target, FileCheck, ClipboardCheck, ArrowRight, Fingerprint, Database, Code2 } from 'lucide-react'
import SpotlightHero from '../components/SpotlightHero'
import AnimatedText from '../components/AnimatedText'
import BentoGrid from '../components/BentoGrid'
import PipelineFlow from '../components/PipelineFlow'
import StatsCard from '../components/StatsCard'

const pageVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.5 } },
  exit: { opacity: 0, transition: { duration: 0.3 } },
}

const bentoItems = [
  {
    icon: <ScanLine className="w-5 h-5" />,
    title: 'Intelligent OCR Pipeline',
    description: 'Native PDFs via PyMuPDF. Scanned pages and photographs routed through Cloud Vision with de-skew, contrast enhancement, and per-page confidence scores.',
  },
  {
    icon: <Brain className="w-5 h-5" />,
    title: 'Two-Stage LLM Extraction',
    description: 'Gemini Flash identifies eligibility sections from ~300 tokens. Gemini Pro extracts structured criteria from full section text. Cross-references trigger gap-fill calls.',
  },
  {
    icon: <Target className="w-5 h-5" />,
    title: 'Vector-Indexed Matching',
    description: 'Per-bidder FAISS indices ensure zero cross-contamination. Type-specific queries retrieve top-3 relevant pages. Regex-first strategy minimizes LLM cost.',
  },
  {
    icon: <Fingerprint className="w-5 h-5" />,
    title: '4-Signal Confidence Scoring',
    description: 'Extraction × OCR × Retrieval × LLM logprob. Calibrated probabilities from Gemini logprob API. No path to silent disqualification — low confidence triggers REVIEW.',
  },
  {
    icon: <FileCheck className="w-5 h-5" />,
    title: 'Cross-Document Validation',
    description: 'Company name consistency, PAN matching, turnover cross-verification (±5%), work order vs completion certificate values (±2%). Any mismatch triggers human review.',
  },
  {
    icon: <ClipboardCheck className="w-5 h-5" />,
    title: 'Complete Audit Trail',
    description: 'Immutable PostgreSQL logs. Full LLM prompt/response capture. SHA-256 document fingerprinting. Version tracking for corrigenda. Exportable PDF reports.',
  },
]

const techStack = [
  { name: 'PyMuPDF', role: 'Native PDF' },
  { name: 'Cloud Vision', role: 'OCR' },
  { name: 'Gemini', role: 'LLM' },
  { name: 'FAISS', role: 'Vectors' },
  { name: 'FastAPI', role: 'Backend' },
  { name: 'React', role: 'Frontend' },
  { name: 'PostgreSQL', role: 'Database' },
]

export default function Landing() {
  return (
    <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit">

      {/* ═══════════ HERO ═══════════ */}
      <SpotlightHero className="min-h-screen flex items-center justify-center relative pt-20 pb-16">
        {/* Dot grid */}
        <div className="absolute inset-0 dot-grid-bg opacity-30" />

        {/* Corner accents */}
        <div className="absolute top-24 left-8 w-16 h-16 border-t border-l border-noir-700/40" />
        <div className="absolute bottom-12 right-8 w-16 h-16 border-b border-r border-noir-700/40" />

        <div className="relative max-w-5xl mx-auto px-6 text-center w-full">

          {/* Headline */}
          <h1 className="font-syne font-extrabold text-4xl md:text-6xl lg:text-7xl text-noir-50 tracking-tighter leading-[1.1] mb-8">
            <span className="block">
              <AnimatedText text="Automate" delay={0.3} />
            </span>
            <span className="block">
              <AnimatedText text="procurement." delay={0.6} />
            </span>
            <span className="block text-amber-500">
              <AnimatedText text="Eliminate" delay={0.9} />
            </span>
            <span className="block">
              <AnimatedText text="ambiguity." delay={1.1} />
            </span>
          </h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5, duration: 0.8 }}
            className="text-lg md:text-xl lg:text-2xl text-noir-300 font-newsreader max-w-4xl mx-auto mb-12 leading-relaxed"
          >
            Three-stage AI pipeline that extracts tender criteria, matches bidder evidence,
            and produces audit-ready verdicts — surfacing only genuine ambiguity for human judgement.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.8 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6"
          >
            <Link
              to="/dashboard"
              className="group flex items-center gap-3 px-8 py-4 bg-amber-500 text-noir-950 font-syne font-bold text-sm sm:text-base tracking-wide hover:bg-amber-400 transition-colors w-full sm:w-auto justify-center"
            >
              BEGIN EVALUATION
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/tender"
              className="flex items-center gap-3 px-8 py-4 border border-noir-600 text-noir-200 font-syne font-bold text-sm sm:text-base tracking-wide hover:border-noir-400 hover:text-noir-50 transition-colors w-full sm:w-auto justify-center"
            >
              UPLOAD TENDER
            </Link>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-px h-16 bg-gradient-to-b from-transparent via-noir-700 to-transparent" />
        </motion.div>
      </SpotlightHero>

      {/* ═══════════ PIPELINE ═══════════ */}
      <section className="py-16 md:py-20 px-6 lg:px-8 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-12 md:mb-16"
        >
          <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-4">
            HOW IT WORKS
          </span>
          <h2 className="font-syne font-bold text-3xl md:text-4xl lg:text-5xl text-noir-50 tracking-tight">
            Three-Stage Pipeline
          </h2>
        </motion.div>
        <PipelineFlow />
      </section>

      {/* ═══════════ DIVIDER ═══════════ */}
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="h-px bg-noir-800" />
      </div>

      {/* ═══════════ BENTO FEATURES ═══════════ */}
      <section className="py-16 md:py-20 px-6 lg:px-8 max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-12 md:mb-16"
        >
          <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-4">
            CAPABILITIES
          </span>
          <h2 className="font-syne font-bold text-3xl md:text-4xl lg:text-5xl text-noir-50 tracking-tight">
            Built for Rigour
          </h2>
        </motion.div>
        <BentoGrid items={bentoItems} />
      </section>

      {/* ═══════════ FOOTER CTA ═══════════ */}
      <section className="py-16 md:py-20 px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-syne font-bold text-3xl md:text-4xl lg:text-5xl text-noir-50 tracking-tight mb-6">
            Every verdict, explained.
          </h2>
          <p className="text-noir-300 font-newsreader text-base md:text-lg lg:text-xl mb-10 leading-relaxed">
            No black boxes. Every decision includes the criterion checked, the document page used,
            the value extracted, the method, and a full confidence breakdown.
          </p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-3 px-8 md:px-10 py-4 bg-amber-500 text-noir-950 font-syne font-bold text-sm md:text-base tracking-wide hover:bg-amber-400 transition-colors"
          >
            ENTER DASHBOARD
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer bar */}
      <footer className="border-t border-noir-800 py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-amber-500/60" />
            <span className="text-xs font-mono text-noir-500">ProcureCheck v1.0</span>
          </div>
          <span className="text-xs text-noir-600 font-newsreader">
            Built for government procurement compliance
          </span>
        </div>
      </footer>
    </motion.div>
  )
}
