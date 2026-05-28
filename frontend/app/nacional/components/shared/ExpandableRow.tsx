'use client'

import { useState } from 'react'
import { Opportunity } from '../../types'

interface ExpandableRowProps {
  opportunity: Opportunity
  onStateChange: (newState: string) => Promise<void>
  onAddNote: (note: string) => Promise<void>
}

export default function ExpandableRow({
  opportunity,
  onStateChange,
  onAddNote,
}: ExpandableRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [noteText, setNoteText] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleStateChange = async (newState: string) => {
    if (!newState) return
    setIsLoading(true)
    try {
      await onStateChange(newState)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddNote = async () => {
    if (!noteText.trim()) return
    setIsLoading(true)
    try {
      await onAddNote(noteText)
      setNoteText('')
    } finally {
      setIsLoading(false)
    }
  }

  const statusBg: Record<string, string> = {
    detected: 'rgba(241,245,249,1)',
    reviewed: 'rgba(37,99,235,0.08)',
    in_crm: 'rgba(5,150,105,0.08)',
    discarded: 'rgba(124,58,237,0.08)',
  }

  const statusColor: Record<string, string> = {
    detected: '#64748B',
    reviewed: '#2563EB',
    in_crm: '#059669',
    discarded: '#7C3AED',
  }

  const urgencyColor: Record<string, string> = {
    high: '#DC2626',
    medium: '#D97706',
    low: '#F59E0B',
  }

  const urgencyLabel = (urgency: string) => {
    switch (urgency) {
      case 'high':
        return '🔴'
      case 'medium':
        return '🟠'
      case 'low':
        return '🟡'
      default:
        return ''
    }
  }

  return (
    <>
      <tr
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          borderBottom: '1px solid var(--border)',
          cursor: 'pointer',
          backgroundColor: 'transparent',
          transition: 'background-color 0.15s',
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg3)'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        <td style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 500, color: 'var(--text)' }}>{opportunity.title}</td>
        <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text)' }}>{opportunity.funder_name}</td>
        <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text)' }}>
          ${(opportunity.amount_max_cop || 0).toLocaleString('es-CO')}
        </td>
        <td style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text)' }}>
          {opportunity.deadline
            ? new Date(opportunity.deadline).toLocaleDateString('es-CO')
            : 'N/A'}
        </td>
        <td style={{ padding: '12px 16px' }}>
          <span
            style={{
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 600,
              backgroundColor: statusBg[opportunity.status] || 'var(--bg3)',
              color: statusColor[opportunity.status] || 'var(--muted)',
            }}
          >
            {opportunity.status}
          </span>
        </td>
        <td style={{ padding: '12px 16px', fontSize: '13px', fontWeight: 700, color: urgencyColor[opportunity.urgency] }}>
          {urgencyLabel(opportunity.urgency)}
        </td>
        <td style={{ padding: '12px 16px', textAlign: 'center' }}>
          <button
            style={{ fontSize: '16px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text)' }}
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </td>
      </tr>

      {isExpanded && (
        <tr style={{ backgroundColor: 'var(--bg3)', borderBottom: '1px solid var(--border)' }}>
          <td colSpan={7} style={{ padding: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <p style={{ fontSize: '11px', fontWeight: 600, color: 'var(--muted)', marginBottom: '4px' }}>Descripción</p>
                <p style={{ fontSize: '13px', color: 'var(--text)' }}>
                  {opportunity.description || 'Sin descripción'}
                </p>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <select
                  disabled={isLoading}
                  onChange={(e) => handleStateChange(e.target.value)}
                  style={{
                    padding: '6px 8px',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    fontSize: '11px',
                    color: 'var(--text)',
                    backgroundColor: 'var(--bg2)',
                    cursor: 'pointer',
                    opacity: isLoading ? 0.5 : 1,
                  }}
                >
                  <option value="">Cambiar estado</option>
                  <option value="detected">Detectada</option>
                  <option value="reviewed">Revisada</option>
                  <option value="in_crm">En gestión</option>
                  <option value="discarded">Descartada</option>
                </select>

                <input
                  type="text"
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Agregar nota..."
                  disabled={isLoading}
                  style={{
                    flex: 1,
                    padding: '6px 8px',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    fontSize: '11px',
                    color: 'var(--text)',
                    backgroundColor: 'var(--bg2)',
                    opacity: isLoading ? 0.5 : 1,
                  }}
                />

                <button
                  onClick={handleAddNote}
                  disabled={isLoading || !noteText.trim()}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: isLoading || !noteText.trim() ? 'var(--muted2)' : 'var(--blue)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: isLoading || !noteText.trim() ? 'not-allowed' : 'pointer',
                    opacity: isLoading || !noteText.trim() ? 0.6 : 1,
                  }}
                >
                  {isLoading ? '...' : 'Agregar'}
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
