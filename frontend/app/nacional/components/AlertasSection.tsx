import { Opportunity, Alert } from '../types'
import { generateAlerts } from '../data/nacional-queries'
import OpportunityCard from './shared/OpportunityCard'

interface AlertasSectionProps {
  opportunities: Opportunity[]
}

export default function AlertasSection({
  opportunities,
}: AlertasSectionProps) {
  const alerts = generateAlerts(opportunities)
  const vencimientos = alerts.filter((a) => a.type === 'vencimiento')

  const groupedByUrgency = {
    high: vencimientos.filter((a) => a.urgency === 'high'),
    medium: vencimientos.filter((a) => a.urgency === 'medium'),
    low: vencimientos.filter((a) => a.urgency === 'low'),
  }

  const getOpportunity = (id: string) =>
    opportunities.find((o) => o.id === id)

  return (
    <div className="page">
      <div className="section-hd">
        <h2>Alertas</h2>
      </div>

      {/* Vencimientos próximos */}
      <div style={{ marginBottom: 32 }}>
        <div className="section-hd" style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 14, fontWeight: 500 }}>Vencimientos próximos</h3>
        </div>

        {vencimientos.length === 0 ? (
          <div className="empty-state">
            No hay alertas de vencimiento
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* 7 días */}
            {groupedByUrgency.high.length > 0 && (
              <div>
                <div className="section-hd" style={{ marginBottom: 12 }}>
                  <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--no)' }}>
                    🔴 Vence en 7 días ({groupedByUrgency.high.length})
                  </h3>
                </div>
                <div className="opp-grid">
                  {groupedByUrgency.high.map((alert) => {
                    const opp = getOpportunity(alert.opportunityId)
                    return opp ? (
                      <OpportunityCard
                        key={opp.id}
                        opportunity={opp}
                      />
                    ) : null
                  })}
                </div>
              </div>
            )}

            {/* 15 días */}
            {groupedByUrgency.medium.length > 0 && (
              <div>
                <div className="section-hd" style={{ marginBottom: 12 }}>
                  <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--amber)' }}>
                    🟠 Vence en 15 días ({groupedByUrgency.medium.length})
                  </h3>
                </div>
                <div className="opp-grid">
                  {groupedByUrgency.medium.map((alert) => {
                    const opp = getOpportunity(alert.opportunityId)
                    return opp ? (
                      <OpportunityCard
                        key={opp.id}
                        opportunity={opp}
                      />
                    ) : null
                  })}
                </div>
              </div>
            )}

            {/* 30 días */}
            {groupedByUrgency.low.length > 0 && (
              <div>
                <div className="section-hd" style={{ marginBottom: 12 }}>
                  <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--blue)' }}>
                    🟡 Vence en 30 días ({groupedByUrgency.low.length})
                  </h3>
                </div>
                <div className="opp-grid">
                  {groupedByUrgency.low.map((alert) => {
                    const opp = getOpportunity(alert.opportunityId)
                    return opp ? (
                      <OpportunityCard
                        key={opp.id}
                        opportunity={opp}
                      />
                    ) : null
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Cambios recientes */}
      <div>
        <div className="section-hd" style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 14, fontWeight: 500 }}>Cambios recientes</h3>
        </div>
        <div className="empty-state">
          No hay cambios recientes registrados
        </div>
      </div>
    </div>
  )
}
