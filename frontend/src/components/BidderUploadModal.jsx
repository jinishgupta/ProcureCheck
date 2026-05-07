import { useState } from 'react'
import { motion } from 'framer-motion'
import { X, Upload, CheckCircle2 } from 'lucide-react'
import FileUpload from './FileUpload'
import { createBidder, uploadBidderDocuments } from '../api'

export default function BidderUploadModal({ tenderId, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    location: '',
  })
  const [files, setFiles] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [step, setStep] = useState(0) // 0=idle, 1=creating, 2=uploading, 3=done
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsProcessing(true)
    setError(null)

    try {
      setStep(1)
      const newBidder = await createBidder({
        tenderId,
        name: formData.name,
        location: formData.location
      })

      setStep(2)
      await uploadBidderDocuments(newBidder.id, files)

      setStep(3)
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 1000)
    } catch (err) {
      console.error('Bidder upload error:', err)
      setError(err.message || 'An error occurred during upload')
      setIsProcessing(false)
      setStep(0)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-noir-950/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-noir-900 border border-noir-800 p-6 w-full max-w-lg shadow-2xl"
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="font-syne font-bold text-xl text-noir-50">Upload Bidder</h2>
          <button onClick={onClose} className="text-noir-500 hover:text-noir-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="border border-crimson-700/30 bg-crimson-900/10 p-3 mb-6 text-sm text-crimson-400 font-mono">
            Error: {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-mono text-noir-400 mb-2">Bidder Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-noir-850 border border-noir-700 px-3 py-2 text-noir-100 font-newsreader focus:outline-none focus:border-amber-500 transition-colors"
              placeholder="e.g., Armour Systems Pvt Ltd"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-noir-400 mb-2">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full bg-noir-850 border border-noir-700 px-3 py-2 text-noir-100 font-newsreader focus:outline-none focus:border-amber-500 transition-colors"
              placeholder="e.g., New Delhi, India"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-noir-400 mb-2">Bidder Documents *</label>
            <FileUpload 
              onFilesSelected={setFiles}
              accept=".pdf,.zip"
              multiple={true}
            />
            <p className="text-[10px] text-noir-500 font-mono mt-2">
              Upload all certificates, test reports, and financial documents (PDF or ZIP).
            </p>
          </div>

          {isProcessing && (
            <div className="bg-noir-950 border border-amber-900/40 p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-xs font-mono text-amber-500">Processing upload...</span>
              </div>
              <div className="space-y-1 text-xs text-noir-400 font-mono ml-6">
                <div className="flex items-center gap-2">
                  {step > 1 ? <CheckCircle2 className="w-3 h-3 text-jade-500" /> : step === 1 ? '•' : ''}
                  <span className={step >= 1 ? 'text-noir-200' : ''}>Creating bidder record</span>
                </div>
                <div className="flex items-center gap-2">
                  {step > 2 ? <CheckCircle2 className="w-3 h-3 text-jade-500" /> : step === 2 ? '•' : ''}
                  <span className={step >= 2 ? 'text-noir-200' : ''}>Uploading documents ({files.length} files)</span>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t border-noir-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isProcessing}
              className="px-4 py-2 text-xs font-mono text-noir-400 hover:text-noir-200"
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={isProcessing || !formData.name || files.length === 0}
              className="flex items-center gap-2 px-5 py-2 bg-amber-500 text-noir-950 text-xs font-mono font-bold hover:bg-amber-400 disabled:opacity-50"
            >
              <Upload className="w-3 h-3" />
              UPLOAD
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}
