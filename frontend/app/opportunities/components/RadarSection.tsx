'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Opportunity, OpportunityList } from '../types'

interface RadarSectionProps {
  initialList: OpportunityList | null
}

const WINDOW_LABEL: Record<string, string> = {
  funding_colombia: 'Funding Colombia',
  funding_global:   'Funding Global',
  strategic:        'Estratégico',
  latam:            'LATAM',
}

function decodeHtml(s: string): string {
  return s
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&rsquo;/g, "'")
    .replace(/&lsquo;/g, "'")
    .replace(/&ldquo;/g, '"')
    .replace(/&rdquo;/g, '"')
    .replace(/&nbsp;/g, ' ')
}

function formatAmount(opp: Opportunity): string {
  const v = opp.amount_max_cop ?? opp.amount_min_cop
  if (!v) return 'Monto no especificado'
  if (v >= 1_000_000_000) return `COP $${(v / 1_000_000_000).toFixed(2)}B`
  if (v >= 1_000_000) return `COP $${Math.round(v / 1_000_000)}M`
  return `COP $${v.toLocaleString()}`
}

function scoreBarClass(score: number | null): string {
  if (score === null) return ''
  if (score >= 6) return 'sf-go'
  if (score >= 4) return 'sf-warn'
  return 'sf-no'
}

function scoreCircleClass(score: number | null): string {
  if (score === null) return ''
  if (score >= 6) return 'sc-go'
  if (score >= 4) return 'sc-warn'
  return 'sc-no'
}

export default function RadarSection({ initialList }: RadarSectionProps) {
  const [decisionFilter, setDecisionFilter] = useState('all')
  const [urgencyFilter, setUrgencyFilter]   = useState('all')
  const [windowFilter, setWindowFilter]     = useState('all')

  if (!initialList || initialList.items.length === 0) {
    return (
      <div className="page">
        <div className="empty-state">
          <strong>Sin oportunidades.</strong><br />
          Corre el scraper para detectar nuevas oportunidades.
        </div>
      </div>
    )
  }

  const items = initialList.items
  const goCount      = items.filter(o => o.decision === 'go').length
  const pendingCount = items.filter(o => o.decision === 'pending').length
  const noGoCount    = items.filter(o => o.decision === 'no_go').length

  const filtered = items.filter(opp => {
    if (decisionFilter !== 'all' && opp.decision !== decisionFilter) return false
    if (urgencyFilter  !== 'all' && opp.urgency   !== urgencyFilter)  return false
    if (windowFilter   !== 'all' && opp.market_window !== windowFilter) return false
    return true
  })

  return (
    <div className="page">
      {/* KPIs */}
      <div className="kpi-row">
        <div className="kpi">
          <div className="kpi-label">Detectadas</div>
          <div className="kpi-val">{items.length}</div>
        </div>
        <div className="kpi go">
          <div className="kpi-label">GO</div>
          <div className="kpi-val go">{goCount}</div>
        </div>
        <div className="kpi warn">
          <div className="kpi-label">Pendientes</div>
          <div className="kpi-val warn">{pendingCount}</div>
        </div>
        <div className="kpi red">
          <div className="kpi-label">No-Go</div>
          <div className="kpi-val red">{noGoCount}</div>
        </div>
      </div>

      {/* Filtros */}
      <div className="filters">
        {(['all', 'go', 'pending', 'no_go'] as const).map(d => (
          <button
            key={d}
            className={`filter-btn${decisionFilter === d ? ' on' : ''}`}
            onClick={() => setDecisionFilter(d)}
          >
            {d === 'all' ? 'Todos' : d === 'go' ? 'GO' : d === 'pending' ? 'Pendiente' : 'No-Go'}
          </button>
        ))}
        <span style={{ color: 'var(--border2)', margin: '0 4px' }}>|</span>
        {(['all', 'high', 'medium', 'low'] as const).map(u => (
          <button
            key={u}
            className={`filter-btn${urgencyFilter === u ? ' on' : ''}`}
            onClick={() => setUrgencyFilter(u)}
          >
            {u === 'all' ? 'Urgencia' : u === 'high' ? '🔴 Alta' : u === 'medium' ? '🟠 Media' : '🟡 Baja'}
          </button>
        ))}
        <span style={{ color: 'var(--border2)', margin: '0 4px' }}>|</span>
        {(['all', 'funding_colombia', 'funding_global', 'strategic', 'latam'] as const).map(w => (
          <button
            key={w}
            className={`filter-btn${windowFilter === w ? ' on' : ''}`}
            onClick={() => setWindowFilter(w)}
          >
            {w === 'all' ? 'Ventana' : WINDOW_LABEL[w] ?? w}
          </button>
        ))}
      </div>

      {/* Grid de cards */}
      {filtered.length === 0 ? (
        <div className="empty-state">Sin resultados para los filtros seleccionados.</div>
      ) : (
        <div className="opp-grid">
          {filtered.map(opp => {
            const title       = decodeHtml(opp.title)
            const description = opp.description ? decodeHtml(opp.description) : null
            const sc          = scoreCircleClass(opp.score_total)
            const sf          = scoreBarClass(opp.score_total)
            const details     = opp.score_details

            const cardClass = opp.decision === 'go'
              ? 'opp-card go-card'
              : opp.decision === 'no_go'
              ? 'opp-card nogo-card'
              : 'opp-card pend-card'

            return (
              <div key={opp.id} className={cardClass}>
                <div className="opp-top">
                  <div style={{ flex: 1 }}>
                    <Link
                      href={`/opportunities/${opp.id}`}
                      className="opp-title"
                      style={{ textDecoration: 'none', display: 'block' }}
                    >
                      {title}
                    </Link>
                  </div>
                  <div className={`score-circle ${sc}`}>
                    {opp.score_total != null ? `${opp.score_total}/10` : '—'}
                  </div>
                </div>

                {description && (
                  <div className="opp-desc">
                    {description.length > 220 ? description.slice(0, 220) + '…' : description}
                  </div>
                )}

                {/* Score bar */}
                {opp.score_total != null && (
                  <div className="score-bar">
                    <div
                      className={`score-fill ${sf}`}
                      style={{ width: `${(opp.score_total / 10) * 100}%` }}
                    />
                  </div>
                )}

                {/* Criteria pills */}
                {details && (
                  <div className="criteria-row">
                    {([1, 2, 3, 4, 5] as const).map(i => {
                      const key = `c${i}` as 'c1' | 'c2' | 'c3' | 'c4' | 'c5'
                      const val = details[key]
                      if (val === undefined) return null
                      return (
                        <span key={i} className={`crit crit-${val}`}>
                          C{i}:{val}
                        </span>
                      )
                    })}
                  </div>
                )}

                <div className="opp-meta">
                  {opp.market_window && (
                    <span className="tag tag-window">{WINDOW_LABEL[opp.market_window] ?? opp.market_window}</span>
                  )}
                  {opp.capital_type && (
                    <span className="tag tag-capital">{opp.capital_type}</span>
                  )}
                  {opp.urgency === 'high' && <span className="tag tag-urgent">URGENTE</span>}
                </div>

                <div className="opp-bottom">
                  <div className="opp-amount">{formatAmount(opp)}</div>
                  {opp.deadline && (
                    <div className="opp-deadline">
                      {new Date(opp.deadline).toLocaleDateString('es-CO', {
                        day: '2-digit', month: 'short', year: 'numeric',
                      })}
                    </div>
                  )}
                </div>

                {/* Contacto rápido */}
                {(opp.url_rfp || opp.ceo_email || opp.org_email) && (
                  <div className="opp-links">
                    {opp.url_rfp && (
                      <a href={opp.url_rfp} target="_blank" rel="noopener noreferrer" className="link-btn primary">
                        ↗ Ver convocatoria
                      </a>
                    )}
                    {(opp.ceo_email || opp.org_email) && (
                      <a
                        href={`mailto:${opp.ceo_email ?? opp.org_email}`}
                        className="link-btn"
                      >
                        ✉ Contactar
                      </a>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
