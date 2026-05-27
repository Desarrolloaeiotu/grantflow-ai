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
    <div className="p-6 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Alertas</h1>

      {/* Vencimientos próximos */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Vencimientos próximos
        </h2>

        {vencimientos.length === 0 ? (
          <p className="text-gray-600 text-center py-8">
            No hay alertas de vencimiento
          </p>
        ) : (
          <div className="space-y-6">
            {/* 7 días */}
            {groupedByUrgency.high.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-red-700 mb-3">
                  🔴 Vence en 7 días ({groupedByUrgency.high.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                <h3 className="text-sm font-semibold text-orange-700 mb-3">
                  🟠 Vence en 15 días ({groupedByUrgency.medium.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                <h3 className="text-sm font-semibold text-yellow-700 mb-3">
                  🟡 Vence en 30 días ({groupedByUrgency.low.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Cambios recientes
        </h2>
        <p className="text-gray-600 text-center py-8">
          No hay cambios recientes registrados
        </p>
      </div>
    </div>
  )
}
