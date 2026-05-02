import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import TenderWorkspace from './pages/TenderWorkspace'
import NewTender from './pages/NewTender'

function App() {
  const location = useLocation()

  return (
    <div className="noise-overlay min-h-screen">
      <Navbar />
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/tender/new" element={<NewTender />} />
          <Route path="/tender/:tenderId" element={<TenderWorkspace />} />
        </Routes>
      </AnimatePresence>
    </div>
  )
}

export default App
