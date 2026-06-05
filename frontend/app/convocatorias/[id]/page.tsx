'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Tender, formatCOP, formatDate, daysUntilDeadline } from '@/app/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function TenderDetailPage() {
  const params = useParams()
  const id = (params?.id as string) || ''

  const [tender, setTender] = useState<Tender | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    fetchTender()
  }, [id])

  async function fetchTender() {
    try {
      const res = await fetch(`${API_URL}/api/v1/tenders/${id}`)
      if (!res.ok) throw new Error('Convocatoria no encontrada')
      const data = await res.json()
      setTender(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="page" style={{ textAlign: 'center', padding: '40px' }}>Cargando...</div>
  if (error || !tender) return <div className="page" style={{ textAlign: 'center', padding: '40px', color: 'var(--nogo)' }}>Error: {error}</div>

  const daysLeft = daysUntilDeadline(tender.deadline)
  const scoreColor = tender.score_total ? (tender.score_total >= 6 ? 'var(--go)' : tender.score_total >= 4 ? '#ff9800' : 'var(--nogo)') : 'var(--muted)'
  const scoreLabel = tender.score_total ? (tender.score_total >= 6 ? 'ALTO' : tender.score_total >= 4 ? 'MEDIO' : 'BAJO') : 'SIN EVALUAR'

  return (
    <div className="page">
      {/* Header */}
      <div style={{
        background: 'var(--bg2)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r)',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '20px', alignItems: 'start' }}>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text)' }}>
              {tender.title}
            </h1>
            <p style={{ fontSize: '12px', color: 'var(--muted)', margin: 0 }}>
              {tender.funder_name}
            </p>
          </div>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            width: '80px',
            height: '80px',
            borderRadius: '8px',
            background: 'var(--border)',
            position: 'relative'
          }}>
            <div style={{
              position: 'absolute',
              inset: 0,
              background: scoreColor,
              opacity: 0.1,
              borderRadius: '8px'
            }} />
            <div style={{
              fontSize: '32px',
              fontWeight: 700,
              color: scoreColor,
              fontFamily: 'monospace',
              zIndex: 1
            }}>
              {tender.score_total || '—'}
            </div>
            <div style={{
              fontSize: '10px',
              color: 'var(--muted)',
              fontWeight: 600,
              zIndex: 1
            }}>
              {scoreLabel}
            </div>
          </div>
        </div>
      </div>

      {/* Metadata */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: '12px',
        marginBottom: '20px'
      }}>
        <div style={{
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r)',
          padding: '12px'
        }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '4px' }}>MONTO MÁXIMO</div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>
            {tender.amount_max_cop ? formatCOP(tender.amount_max_cop) : '—'}
          </div>
        </div>

        <div style={{
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r)',
          padding: '12px'
        }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '4px' }}>CIERRE</div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>
            {formatDate(tender.deadline) || '—'}
          </div>
          {daysLeft && (
            <div style={{ fontSize: '10px', color: daysLeft <= 7 ? 'var(--nogo)' : 'var(--muted)', marginTop: '4px' }}>
              {daysLeft} días
            </div>
          )}
        </div>

        <div style={{
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r)',
          padding: '12px'
        }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '4px' }}>DECISIÓN</div>
          <div style={{
            fontSize: '12px',
            fontWeight: 700,
            color: tender.decision === 'go' ? 'var(--go)' : tender.decision === 'no_go' ? 'var(--nogo)' : 'var(--muted)'
          }}>
            {tender.decision?.toUpperCase() || 'PENDIENTE'}
          </div>
        </div>
      </div>

      {/* Descripción */}
      {tender.description && (
        <div style={{
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--r)',
          padding: '12px',
          marginBottom: '20px'
        }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '8px', paddingBottom: '8px', borderBottom: '1px solid var(--border)' }}>
            DESCRIPCIÓN
          </div>
          <p style={{ fontSize: '12px', lineHeight: 1.6, color: 'var(--text)', margin: 0 }}>
            {tender.description}
          </p>
        </div>
      )}

      {/* Links */}
      <div style={{ display: 'flex', gap: '12px' }}>
        {tender.url_rfp && (
          <a href={tender.url_rfp} target="_blank" rel="noopener noreferrer" className="link-btn primary">
            Ver Convocatoria
          </a>
        )}
        {tender.url_tor && (
          <a href={tender.url_tor} target="_blank" rel="noopener noreferrer" className="link-btn">
            Términos de Referencia
          </a>
        )}
        {tender.url_form && (
          <a href={tender.url_form} target="_blank" rel="noopener noreferrer" className="link-btn">
            Formulario
          </a>
        )}
      </div>

      {/* Volver */}
      <div style={{ marginTop: '20px' }}>
        <Link href="/convocatorias" className="link-btn">
          ← Volver a Convocatorias
        </Link>
      </div>
    </div>
  )
}
