// FILE: frontend/src/App.jsx
import React, { useState, useEffect } from 'react'
import RiskDashboard from './pages/RiskDashboard'

export default function App() {
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    // Simple check - just set ready after a short delay
    setTimeout(() => {
      setIsReady(true)
    }, 500)
  }, [])

  if (!isReady) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        fontSize: '18px'
      }}>
        Loading MaatruRaksha AI...
      </div>
    )
  }

  return <RiskDashboard />
}