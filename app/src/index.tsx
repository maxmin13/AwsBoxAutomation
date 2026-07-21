import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
import App from './App'

// Catches errors outside React's render phase (event handlers, timers,
// unhandled promise rejections) that ErrorBoundary can't see, so they still
// reach gui.log instead of only the (usually closed) devtools console.
window.addEventListener('error', (event) => {
  window.electronAPI.logError(event.message, event.error?.stack ?? '')
})

window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason
  window.electronAPI.logError(
    reason instanceof Error ? reason.message : String(reason),
    reason instanceof Error ? (reason.stack ?? '') : '',
  )
})

const root = document.getElementById('root')!
createRoot(root).render(<App />)
