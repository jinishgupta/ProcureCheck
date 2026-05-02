import { Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Shield, Menu, X } from 'lucide-react'

const navLinks = [
  { path: '/', label: 'Home' },
  { path: '/dashboard', label: 'Dashboard' },
]

export default function Navbar() {
  const location = useLocation()
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-noir-950/90 backdrop-blur-xl border-b border-noir-800/60'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-18">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 border border-amber-500/60 flex items-center justify-center group-hover:border-amber-400 transition-colors">
              <Shield className="w-4 h-4 text-amber-500" />
            </div>
            <span className="font-syne font-bold text-base tracking-tight text-noir-50">
              ProcureCheck
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden lg:flex items-center gap-8">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`relative px-2 py-2 text-base font-newsreader transition-colors duration-300 ${
                    isActive
                      ? 'text-amber-400'
                      : 'text-noir-300 hover:text-noir-100'
                  }`}
                >
                  {link.label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-underline"
                      className="absolute bottom-0 left-3 right-3 h-px bg-amber-500"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              )
            })}
          </div>

          {/* Mobile Toggle */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden p-2 text-noir-300 hover:text-noir-100 transition-colors"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="lg:hidden bg-noir-900/95 backdrop-blur-xl border-b border-noir-800 px-6 py-4"
        >
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`block py-2.5 text-sm font-newsreader transition-colors ${
                location.pathname === link.path
                  ? 'text-amber-400'
                  : 'text-noir-300 hover:text-noir-100'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </motion.div>
      )}
    </nav>
  )
}
