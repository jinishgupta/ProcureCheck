import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Upload, FileText, CheckCircle2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import FileUpload from '../components/FileUpload'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
}

export default function NewTender() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    title: '',
    department: '',
    estimatedValue: '',
    issueDate: '',
    closingDate: '',
  })
  const [files, setFiles] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    setIsProcessing(true)
    
    // Simulate processing
    setTimeout(() => {
      // In real app, this would upload and process the tender
      // For now, redirect to the first tender
      navigate('/tender/CRPF-2026-IT-0042')
    }, 2000)
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <motion.div 
      variants={pageVariants} 
      initial="initial" 
      animate="animate" 
      exit="exit" 
      className="pt-32 pb-16 px-6 lg:px-8 max-w-4xl mx-auto"
    >
      {/* Back Button */}
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-2 text-noir-400 hover:text-amber-500 font-mono text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Header */}
      <div className="mb-10">
        <span className="text-xs font-mono text-amber-500 tracking-[0.3em] block mb-3">CREATE NEW</span>
        <h1 className="font-syne font-bold text-3xl md:text-4xl text-noir-50 tracking-tight mb-2">
          Upload Tender Document
        </h1>
        <p className="text-noir-400 font-newsreader">
          Upload a tender document to extract eligibility criteria automatically
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Tender Details */}
        <div className="border border-noir-800 bg-noir-900/60 p-6">
          <h2 className="font-syne font-semibold text-noir-50 text-lg mb-6">Tender Details</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-mono text-noir-300 mb-2">
                Tender Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                className="w-full bg-noir-850 border border-noir-700 px-4 py-3 text-noir-100 font-newsreader focus:outline-none focus:border-amber-500 transition-colors"
                placeholder="e.g., Supply of Ballistic Helmets"
              />
            </div>

            <div>
              <label className="block text-sm font-mono text-noir-300 mb-2">
                Department *
              </label>
              <input
                type="text"
                name="department"
                value={formData.department}
                onChange={handleChange}
                required
                className="w-full bg-noir-850 border border-noir-700 px-4 py-3 text-noir-100 font-newsreader focus:outline-none focus:border-amber-500 transition-colors"
                placeholder="e.g., Central Reserve Police Force"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-mono text-noir-300 mb-2">
                  Estimated Value
                </label>
                <input
                  type="text"
                  name="estimatedValue"
                  value={formData.estimatedValue}
                  onChange={handleChange}
                  className="w-full bg-noir-850 border border-noir-700 px-4 py-3 text-noir-100 font-newsreader focus:outline-none focus:border-amber-500 transition-colors"
                  placeholder="e.g., ₹12.8 Cr"
                />
              </div>

              <div>
                <label className="block text-sm font-mono text-noir-300 mb-2">
                  Issue Date
                </label>
                <input
                  type="date"
                  name="issueDate"
                  value={formData.issueDate}
                  onChange={handleChange}
                  className="w-full bg-noir-850 border border-noir-700 px-4 py-3 text-noir-100 font-mono focus:outline-none focus:border-amber-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-mono text-noir-300 mb-2">
                Closing Date
              </label>
              <input
                type="date"
                name="closingDate"
                value={formData.closingDate}
                onChange={handleChange}
                className="w-full bg-noir-850 border border-noir-700 px-4 py-3 text-noir-100 font-mono focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>
          </div>
        </div>

        {/* File Upload */}
        <div className="border border-noir-800 bg-noir-900/60 p-6">
          <h2 className="font-syne font-semibold text-noir-50 text-lg mb-6">Tender Document</h2>
          <FileUpload 
            onFilesSelected={setFiles}
            accept=".pdf"
            multiple={false}
          />
          <p className="text-xs text-noir-500 font-mono mt-3">
            Upload the complete tender document (PDF format). The system will automatically extract eligibility criteria.
          </p>
        </div>

        {/* Processing Info */}
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="border border-amber-700/30 bg-amber-900/10 p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm font-mono text-amber-400">Processing tender document...</span>
            </div>
            <div className="space-y-2 text-xs text-noir-400 font-mono">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3 h-3 text-jade-500" />
                <span>Classifying pages (native vs scanned)</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3 h-3 text-jade-500" />
                <span>Running OCR on scanned pages</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 border border-amber-500 rounded-full animate-pulse" />
                <span>Extracting eligibility criteria...</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Submit Button */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={isProcessing || !formData.title || !formData.department || files.length === 0}
            className="flex items-center gap-2 px-8 py-4 bg-amber-500 text-noir-950 font-mono font-bold hover:bg-amber-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Upload className="w-4 h-4" />
            {isProcessing ? 'PROCESSING...' : 'UPLOAD & PROCESS'}
          </button>
          
          <Link
            to="/dashboard"
            className="flex items-center gap-2 px-8 py-4 border border-noir-700 text-noir-300 font-mono hover:border-noir-500 hover:text-noir-100 transition-colors"
          >
            CANCEL
          </Link>
        </div>
      </form>
    </motion.div>
  )
}
