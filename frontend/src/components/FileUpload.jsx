import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Upload, FileText, Image, X } from 'lucide-react'

export default function FileUpload({ onFilesSelected, accept = '.pdf,.jpg,.jpeg,.png', multiple = true }) {
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState([])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    setFiles((prev) => [...prev, ...droppedFiles])
    onFilesSelected?.(droppedFiles)
  }, [onFilesSelected])

  const handleFileInput = (e) => {
    const selectedFiles = Array.from(e.target.files)
    setFiles((prev) => [...prev, ...selectedFiles])
    onFilesSelected?.(selectedFiles)
  }

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const getFileIcon = (file) => {
    if (file.type.includes('pdf')) return <FileText className="w-4 h-4 text-crimson-400" />
    if (file.type.includes('image')) return <Image className="w-4 h-4 text-jade-400" />
    return <FileText className="w-4 h-4 text-noir-400" />
  }

  return (
    <div className="space-y-4">
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        animate={{
          borderColor: isDragging ? 'rgba(212, 168, 83, 0.5)' : 'rgba(46, 46, 54, 1)',
        }}
        className="relative border border-dashed border-noir-600 bg-noir-900/40 p-12 flex flex-col items-center justify-center cursor-pointer overflow-hidden group"
        onClick={() => document.getElementById('file-input').click()}
      >
        {/* Dot grid */}
        <div className="absolute inset-0 dot-grid-bg opacity-40" />

        <motion.div
          animate={{ y: isDragging ? -4 : 0 }}
          transition={{ type: 'spring', stiffness: 400 }}
        >
          <Upload className={`w-8 h-8 mb-4 transition-colors duration-300 ${isDragging ? 'text-amber-500' : 'text-noir-500'}`} />
        </motion.div>

        <p className="text-sm text-noir-200 font-syne font-medium mb-1">
          {isDragging ? 'Release to upload' : 'Drop files here or click to browse'}
        </p>
        <p className="text-xs text-noir-500 font-mono">
          PDF, JPG, PNG — Typed or scanned documents
        </p>

        <input
          id="file-input"
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleFileInput}
          className="hidden"
        />
      </motion.div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-1">
          {files.map((file, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-3 p-3 bg-noir-900/60 border border-noir-800 group"
            >
              {getFileIcon(file)}
              <span className="text-sm text-noir-200 flex-1 truncate font-mono">{file.name}</span>
              <span className="text-xs text-noir-500 font-mono">
                {(file.size / 1024).toFixed(0)} KB
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); removeFile(i) }}
                className="text-noir-500 hover:text-crimson-400 transition-colors p-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
