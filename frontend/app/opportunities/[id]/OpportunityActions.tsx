'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface Props {
  opportunityId: string
  initialStatus: string | null
  apiUrl: string
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  detected:  { label: 'Detectada',     color: 'var(--muted2)', bg: 'var(--bg4)' },
  reviewed:  { label: 'En revisión',   color: 'var(--amber)',  bg: 'var(--amber-bg)' },
  in_crm:    { label: 'Enviada al CRM', color: 'var(--blue)',   bg: 'var(--blue-bg)' },
  discarded: { label: 'Descartada',    color: 'var(--nogo)',   bg: 'var(--nogo-bg)' },
}

export default function OpportunityActions({ opportunityId, initialStatus, apiUrl }: Props) {
  const router = useRouter()
  const [status, setStatus] = useState(initialStatus ?? 'detected')
  const [busy, setBusy] = useState(false)
  const [notes, setNotes] = useState('')
  const [savedAt, setSavedAt] = useState<string | null>(null)

  // Notas en localStorage por ahora (Sprint S5 las moverá a la DB)
  useEffect(() => {
    const stored = localStorage.getItem(`opp-notes-${opportunityId}`)
    if (stored) setNotes(stored)
  }, [opportunityId])

  async function changeStatus(newStatus: string) {
    if (busy) return
    setBusy(true)
    try {
      const res = await fetch(`${apiUrl}/api/v1/opportunities/${opportunityId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      })
      if (res.ok) {
        setStatus(newStatus)
        router.refresh()
      } else {
        alert(`Error: ${res.status}`)
      }
    } catch (e) {
      alert(`Error de red: ${e instanceof Error ? e.message : 'unknown'}`)
    } finally {
      setBusy(false)
    }
  }

  function saveNotes() {
    localStorage.setItem(`opp-notes-${opportunityId}`, notes)
    setSavedAt(new Date().toLocaleTimeString('es-CO'))
  }

  const current = STATUS_CONFIG[status] ?? STATUS_CONFIG.detected

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* Acciones de status */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)' }}>
            Acciones CRM · Estado actual
          </div>
          <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 20, fontWeight: 600, color: current.color, background: current.bg, border: `1px solid ${current.color}40` }}>
            {current.label}
          </span>
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {status !== 'reviewed' && (
            <button
              onClick={() => changeStatus('reviewed')}
              disabled={busy}
              className="link-btn"
              style={{ color: 'var(--amber)', borderColor: 'rgba(251,191,36,0.3)', cursor: busy ? 'wait' : 'pointer' }}
            >
              ⏵ Marcar en revisión
            </button>
          )}
          {status !== 'in_crm' && (
            <button
              onClick={() => changeStatus('in_crm')}
              disabled={busy}
              className="link-btn primary"
              style={{ cursor: busy ? 'wait' : 'pointer' }}
            >
              → Enviar al CRM
            </button>
          )}
          {status !== 'discarded' && (
            <button
              onClick={() => changeStatus('discarded')}
              disabled={busy}
              className="link-btn"
              style={{ color: 'var(--nogo)', borderColor: 'rgba(248,113,113,0.3)', cursor: busy ? 'wait' : 'pointer' }}
            >
              ✕ Descartar
            </button>
          )}
          {status !== 'detected' && (
            <button
              onClick={() => changeStatus('detected')}
              disabled={busy}
              className="link-btn"
              style={{ cursor: busy ? 'wait' : 'pointer' }}
            >
              ↺ Reset
            </button>
          )}
        </div>
      </div>

      {/* Notas */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)' }}>
            Notas internas
          </div>
          {savedAt && (
            <span style={{ fontSize: 10, color: 'var(--go)' }}>✓ Guardado {savedAt}</span>
          )}
        </div>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notas del equipo de Alianzas — contactos previos, observaciones, próximos pasos..."
          rows={4}
          style={{
            width: '100%',
            background: 'var(--bg3)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '10px 12px',
            color: 'var(--text)',
            fontFamily: 'var(--sans)',
            fontSize: 12.5,
            resize: 'vertical',
            outline: 'none',
            lineHeight: 1.5,
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
          <span style={{ fontSize: 10, color: 'var(--muted)', fontStyle: 'italic' }}>
            Guardado local · S5 las moverá a la DB
          </span>
          <button
            onClick={saveNotes}
            className="link-btn primary"
            style={{ cursor: 'pointer' }}
          >
            💾 Guardar nota
          </button>
        </div>
      </div>
    </div>
  )
}
