'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

interface RunScraperButtonProps {
  source?: string
  label?: string
  showStatus?: boolean
}

export default function RunScraperButton({
  source = 'nacional_colombia',
  label = '▶ Ejecutar Scraper',
  showStatus = true
}: RunScraperButtonProps) {
  const router = useRouter()
  const [isRunning, setIsRunning] = useState(false)
  const [status, setStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  const handleRunScraper = async () => {
    setIsRunning(true)
    setStatus('running')
    setMessage('Ejecutando scraper...')

    try {
      const apiUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const apiKey: string = process.env.NEXT_PUBLIC_API_KEY || ''

      // Paso 1: Ejecutar scraper con scoring automático
      const sourceParam = source || 'nacional_colombia'
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (apiKey) {
        headers['X-API-Key'] = apiKey
      }

      const scrapeRes = await fetch(`${apiUrl}/api/v1/scrape/run?source=${sourceParam}&score=true`, {
        method: 'POST',
        headers,
      })

      if (!scrapeRes.ok) {
        throw new Error(`Error ${scrapeRes.status}: ${scrapeRes.statusText}`)
      }

      const scrapeData = await scrapeRes.json()
      const newCount = scrapeData.total_persisted || 0

      setStatus('success')
      setMessage(`✓ Completado: ${newCount} nuevas oportunidades`)

      // Recargar página sin filtros después de 1.5 segundos
      setTimeout(() => {
        window.location.href = '/'
      }, 1500)
    } catch (err) {
      setStatus('error')
      setMessage(`✗ Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
      console.error('Scraper error:', err)
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: showStatus ? 16 : 0 }}>
      <button
        onClick={handleRunScraper}
        disabled={isRunning}
        style={{
          padding: '8px 16px',
          background: isRunning ? '#9ca3af' : '#059669',
          color: '#fff',
          border: 'none',
          borderRadius: 6,
          fontSize: 13,
          fontWeight: 600,
          cursor: isRunning ? 'not-allowed' : 'pointer',
          opacity: isRunning ? 0.7 : 1,
          transition: 'all 0.2s',
          whiteSpace: 'nowrap',
        }}
        title="Ejecuta el scraper automático para detectar nuevas oportunidades"
      >
        {isRunning ? '⏳ Scrapeando...' : label}
      </button>

      {showStatus && message && (
        <span style={{
          fontSize: 12,
          color: status === 'success' ? 'var(--go)' : status === 'error' ? 'var(--nogo)' : 'var(--muted)',
          fontFamily: 'var(--mono)',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}>
          {status === 'running' && '⌛'}
          {status === 'success' && '✓'}
          {status === 'error' && '✕'}
          {message}
        </span>
      )}
    </div>
  )
}
