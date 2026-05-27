'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Metrics } from '../types'

interface OpportunitiesSidebarProps {
  metrics: Metrics | null
}

export default function OpportunitiesSidebar({ metrics }: OpportunitiesSidebarProps) {
  const searchParams = useSearchParams()
  const activeSection = searchParams.get('section') || 'radar'

  const sections = [
    { id: 'alertas', label: 'Alertas', icon: '🔔' },
    { id: 'radar',   label: 'Radar',   icon: '📊' },
    { id: 'pipeline', label: 'Pipeline', icon: '📋' },
    { id: 'contactos', label: 'Contactos', icon: '👥' },
  ]

  return (
    <aside style={{
      width: 220,
      borderLeft: '1px solid var(--border)',
      background: 'var(--bg2)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflowY: 'auto',
      flexShrink: 0,
    }}>
      <div className="nav">
        <div className="nav-section">Secciones</div>
        {sections.map((s) => (
          <Link
            key={s.id}
            href={`/?section=${s.id}`}
            className={`nav-item${activeSection === s.id ? ' active' : ''}`}
          >
            <span className="nav-icon">{s.icon}</span>
            {s.label}
            {metrics && s.id === 'radar' && (
              <span className="nav-count">{metrics.total_detected}</span>
            )}
            {metrics && s.id === 'pipeline' && (
              <span className="nav-count">{metrics.total_go}</span>
            )}
          </Link>
        ))}

        {metrics && (
          <>
            <div className="nav-section" style={{ marginTop: 16 }}>Resumen</div>
            <div style={{ padding: '4px 10px', display: 'flex', flexDirection: 'column', gap: 7 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>Detectadas</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{metrics.total_detected}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>GO</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--go)' }}>{metrics.total_go}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>Pendiente</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--amber)' }}>{metrics.total_pending}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>No-Go</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--nogo)' }}>{metrics.total_no_go}</span>
              </div>
            </div>
          </>
        )}
      </div>
    </aside>
  )
}
