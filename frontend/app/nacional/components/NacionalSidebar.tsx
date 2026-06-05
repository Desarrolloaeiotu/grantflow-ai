// frontend/app/nacional/components/NacionalSidebar.tsx

'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { DashboardMetrics } from '../types'

interface NacionalSidebarProps {
  metrics: DashboardMetrics
  alertCount: number
}

export default function NacionalSidebar({
  metrics,
  alertCount,
}: NacionalSidebarProps) {
  const searchParams = useSearchParams()
  const activeSection = searchParams?.get('section') || 'radar'

  const sections = [
    {
      id: 'alertas',
      label: 'Alertas',
      badge: alertCount,
      icon: '🔔',
    },
    {
      id: 'radar',
      label: 'Radar',
      badge: metrics.detected ?? 0,
      icon: '📊',
    },
    {
      id: 'pipeline',
      label: 'Pipeline',
      badge: metrics.in_crm ?? 0,
      icon: '📋',
    },
    {
      id: 'contactos',
      label: 'Contactos',
      badge: 0, // TODO: fetch contact count
      icon: '👥',
    },
  ]

  return (
    <aside style={{ width: 220, borderLeft: '1px solid var(--border)', background: 'var(--bg2)', padding: '14px 10px', height: '100vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
      {/* Secciones de navegación */}
      <nav className="nav" style={{ marginBottom: 16 }}>
        {sections.map((section) => (
          <Link
            key={section.id}
            href={`/nacional?section=${section.id}`}
            className={`nav-item${activeSection === section.id ? ' active' : ''}`}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <span className="nav-icon">{section.icon}</span>
            <span>{section.label}</span>
            {section.badge > 0 && <span className="nav-count">{section.badge}</span>}
          </Link>
        ))}
      </nav>

      {/* Resumen */}
      <div className="nav-section" style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
          Resumen
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--muted)' }}>Detectadas</span>
            <span style={{ fontWeight: 600, color: 'var(--text)' }}>{metrics.detected}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--muted)' }}>Revisadas</span>
            <span style={{ fontWeight: 600, color: 'var(--text)' }}>{metrics.reviewed}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--muted)' }}>En gestión</span>
            <span style={{ fontWeight: 600, color: 'var(--text)' }}>{metrics.in_crm}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: 'var(--muted)' }}>Cerradas</span>
            <span style={{ fontWeight: 600, color: 'var(--text)' }}>{metrics.cerrada}</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
