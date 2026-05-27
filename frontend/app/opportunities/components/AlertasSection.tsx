import Link from 'next/link'
import { Opportunity } from '../types'

interface AlertasSectionProps {
  opportunities: Opportunity[]
}

function daysUntil(deadline: string): number {
  const d = new Date(deadline)
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  return Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
}

function formatAmount(opp: Opportunity): string {
  const v = opp.amount_max_cop ?? opp.amount_min_cop
  if (!v) return 'Monto no especificado'
  if (v >= 1_000_000_000) return `COP $${(v / 1_000_000_000).toFixed(1)}B`
  if (v >= 1_000_000) return `COP $${Math.round(v / 1_000_000)}M`
  return `COP $${v.toLocaleString()}`
}

export default function AlertasSection({ opportunities }: AlertasSectionProps) {
  const alerts = opportunities
    .filter(o => o.deadline)
    .map(o => ({ opp: o, days: daysUntil(o.deadline!) }))
    .filter(({ days }) => days > 0 && days <= 30)
    .sort((a, b) => a.days - b.days)

  const high   = alerts.filter(({ days }) => days <= 7)
  const medium = alerts.filter(({ days }) => days > 7 && days <= 15)
  const low    = alerts.filter(({ days }) => days > 15)

  return (
    <div className="page">
      <div className="kpi-row">
        <div className="kpi">
          <div className="kpi-label">Total alertas</div>
          <div className="kpi-val">{alerts.length}</div>
          <div className="kpi-sub">próximos 30 días</div>
        </div>
        <div className="kpi red">
          <div className="kpi-label">Urgentes ≤7d</div>
          <div className="kpi-val red">{high.length}</div>
        </div>
        <div className="kpi warn">
          <div className="kpi-label">Medias ≤15d</div>
          <div className="kpi-val warn">{medium.length}</div>
        </div>
        <div className="kpi blue">
          <div className="kpi-label">Bajas ≤30d</div>
          <div className="kpi-val blue">{low.length}</div>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="empty-state">
          <strong>Sin alertas de vencimiento.</strong><br />
          No hay oportunidades con cierre en los próximos 30 días.
        </div>
      ) : (
        <>
          {high.length > 0 && (
            <>
              <div className="section-hd">
                <h2>🔴 Urgentes — ≤7 días <em>({high.length})</em></h2>
              </div>
              <div className="opp-grid">
                {high.map(({ opp, days }) => (
                  <AlertCard key={opp.id} opp={opp} days={days} />
                ))}
              </div>
            </>
          )}

          {medium.length > 0 && (
            <>
              <div className="section-hd">
                <h2>🟠 Medias — ≤15 días <em>({medium.length})</em></h2>
              </div>
              <div className="opp-grid">
                {medium.map(({ opp, days }) => (
                  <AlertCard key={opp.id} opp={opp} days={days} />
                ))}
              </div>
            </>
          )}

          {low.length > 0 && (
            <>
              <div className="section-hd">
                <h2>🟡 Bajas — ≤30 días <em>({low.length})</em></h2>
              </div>
              <div className="opp-grid">
                {low.map(({ opp, days }) => (
                  <AlertCard key={opp.id} opp={opp} days={days} />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

function AlertCard({ opp, days }: { opp: Opportunity; days: number }) {
  const isUrgent = days <= 7
  const isMed    = days > 7 && days <= 15

  return (
    <div className={`opp-card${isUrgent ? ' pend-card' : ''}`}>
      <div className="opp-top">
        <div style={{ flex: 1 }}>
          <Link
            href={`/opportunities/${opp.id}`}
            className="opp-title"
            style={{ textDecoration: 'none', display: 'block' }}
          >
            {opp.title.length > 90 ? opp.title.slice(0, 90) + '…' : opp.title}
          </Link>
        </div>
        {opp.score_total != null && (
          <div
            className="score-circle"
            style={{
              background:  opp.decision === 'go' ? 'var(--go-bg)' : 'var(--bg4)',
              color:       opp.decision === 'go' ? 'var(--go)'    : 'var(--text)',
              borderColor: opp.decision === 'go' ? 'var(--go-bdr)' : 'var(--border2)',
            }}
          >
            {opp.score_total}/10
          </div>
        )}
      </div>

      <div className="opp-meta">
        {opp.market_window && (
          <span className="tag tag-window">{opp.market_window.replace('_', ' ')}</span>
        )}
        {opp.capital_type && (
          <span className="tag tag-capital">{opp.capital_type}</span>
        )}
        {isUrgent && <span className="tag tag-urgent">URGENTE</span>}
      </div>

      <div className="opp-bottom">
        <div className="opp-amount">{formatAmount(opp)}</div>
        <div className={isUrgent ? 'deadline-urgent' : isMed ? 'deadline-med' : 'opp-deadline'}>
          Vence en {days} día{days !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  )
}
