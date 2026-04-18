import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Router } from './router.tsx'
import './styles/globals.css'

async function enableMocking() {
  if (import.meta.env.MODE !== 'development') {
    return
  }

  const { worker } = await import('./mocks/browser')

  // `worker.start()` returns a Promise that resolves
  // once the Service Worker is up and running.
  return worker.start()
}

enableMocking().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <Router />
    </StrictMode>,
  )
})
