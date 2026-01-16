import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initWebVitals } from './utils/webVitals'

// Initialize Web Vitals performance monitoring
initWebVitals({
  debug: import.meta.env.DEV,
  sampleRate: 1.0, // Report 100% of metrics in development, adjust for production
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
