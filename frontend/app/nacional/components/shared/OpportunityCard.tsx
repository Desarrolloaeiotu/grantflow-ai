import { Opportunity } from '../../types'

interface OpportunityCardProps {
  opportunity: Opportunity
  onClick?: () => void
}

const urgencyBadge = {
  high: { bg: 'bg-red-100', text: 'text-red-700', icon: '🔴' },
  medium: { bg: 'bg-orange-100', text: 'text-orange-700', icon: '🟠' },
  low: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: '🟡' },
}

const decisionBadge = {
  go: { bg: 'bg-green-100', text: 'text-green-700', label: 'GO' },
  no_go: { bg: 'bg-red-100', text: 'text-red-700', label: 'NO GO' },
  pending: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Pendiente' },
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
      className="p-4 border border-gray-200 rounded-lg bg-white hover:shadow-md cursor-pointer transition"
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-sm text-gray-900 flex-1">
          {opportunity.title}
        </h3>
        <span className={`px-2 py-1 rounded text-xs font-medium ${badge.bg} ${badge.text}`}>
          {badge.icon} {urgencyDays[opportunity.urgency]}
        </span>
      </div>

      <p className="text-xs text-gray-600 mb-3">{opportunity.funder_name}</p>

      <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
        <div>
          <span className="font-semibold text-gray-700">Monto:</span>
          <p className="text-gray-600">
            ${(opportunity.amount_max_cop || 0).toLocaleString('es-CO')}
          </p>
        </div>
        <div>
          <span className="font-semibold text-gray-700">Vencimiento:</span>
          <p className="text-gray-600">
            {opportunity.deadline
              ? new Date(opportunity.deadline).toLocaleDateString('es-CO')
              : 'N/A'}
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
          {opportunity.status}
        </span>
        {opportunity.decision !== 'pending' && (
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${decBadge.bg} ${decBadge.text}`}
          >
            {decBadge.label}
          </span>
        )}
      </div>
    </div>
  )
}
