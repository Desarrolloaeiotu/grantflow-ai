import { Opportunity } from '../../types'

interface OpportunityCardProps {
  opportunity: Opportunity
  onClick?: () => void
}

const urgencyBadge = {
  high: { bg: '#DC2626', bgLight: 'rgba(220,38,38,0.08)', icon: '🔴' },
  medium: { bg: '#D97706', bgLight: 'rgba(217,119,6,0.08)', icon: '🟠' },
  low: { bg: '#F59E0B', bgLight: 'rgba(245,158,11,0.08)', icon: '🟡' },
}

const decisionBadge = {
  go: { bg: '#059669', bgLight: 'rgba(5,150,105,0.08)', label: 'GO' },
  no_go: { bg: '#DC2626', bgLight: 'rgba(220,38,38,0.08)', label: 'NO GO' },
  pending: { bg: '#64748B', bgLight: 'rgba(100,116,139,0.08)', label: 'Pendiente' },
}

export default function OpportunityCard({
  opportunity,
  onClick,
}: OpportunityCardProps) {
  const badge = urgencyBadge[opportunity.urgency]
  const decBadge = decisionBadge[opportunity.decision]

  const urgencyDays = {
    high: '7d',
    medium: '15d',
    low: '30d',
  }

  return (
    <div
      onClick={onClick}
      style={{
        padding: '16px',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r)',
        backgroundColor: 'var(--bg2)',
        cursor: 'pointer',
        transition: 'box-shadow 0.2s, transform 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <h3 style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text)', flex: 1 }}>
          {opportunity.title}
        </h3>
        <span
          style={{
            padding: '4px 8px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            backgroundColor: badge.bgLight,
            color: badge.bg,
            marginLeft: '8px',
            whiteSpace: 'nowrap',
          }}
        >
          {badge.icon} {urgencyDays[opportunity.urgency]}
        </span>
      </div>

      <p style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '12px' }}>{opportunity.funder_name}</p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px', fontSize: '11px' }}>
        <div>
          <span style={{ fontWeight: 600, color: 'var(--text)' }}>Monto:</span>
          <p style={{ color: 'var(--muted)', marginTop: '2px' }}>
            ${(opportunity.amount_max_cop || 0).toLocaleString('es-CO')}
          </p>
        </div>
        <div>
          <span style={{ fontWeight: 600, color: 'var(--text)' }}>Vencimiento:</span>
          <p style={{ color: 'var(--muted)', marginTop: '2px' }}>
            {opportunity.deadline
              ? new Date(opportunity.deadline).toLocaleDateString('es-CO')
              : 'N/A'}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <span
          style={{
            padding: '4px 8px',
            backgroundColor: 'var(--blue-bg)',
            color: 'var(--blue)',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
          }}
        >
          {opportunity.status}
        </span>
        {opportunity.decision !== 'pending' && (
          <span
            style={{
              padding: '4px 8px',
              backgroundColor: decBadge.bgLight,
              color: decBadge.bg,
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 600,
            }}
          >
            {decBadge.label}
          </span>
        )}
      </div>
    </div>
  )
}
