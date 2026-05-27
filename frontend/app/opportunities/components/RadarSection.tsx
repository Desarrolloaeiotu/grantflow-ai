'use client'

import Link from 'next/link'
import { Opportunity, OpportunityList } from '../types'

interface RadarSectionProps {
  initialList: OpportunityList | null
}

const WINDOW_LABEL: Record<string, string> = {
  funding_colombia: 'Funding Colombia',
  funding_global: 'Funding Global',
  strategic: 'Estrategico',
  latam: 'LATAM',
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

export default function RadarSection({ initialList }: RadarSectionProps) {
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

  return (
    <div className="page">
      <div className="opp-grid">
        {initialList.items.map((opp) => {
          const title = decodeHtml(opp.title)
          const description = opp.description ? decodeHtml(opp.description) : null

          return (
            <div key={opp.id} className="opp-card">
              <div className="opp-top">
                <div style={{ flex: 1 }}>
                  <Link href={`/opportunities/${opp.id}`} className="opp-title" style={{ textDecoration: 'none', display: 'block' }}>
                    {title}
                  </Link>
                </div>
                <div className="score-circle" style={{
                  background: opp.decision === 'go' ? 'var(--go-bg)' : 'var(--bg4)',
                  color: opp.decision === 'go' ? 'var(--go)' : 'var(--text)'
                }}>
                  {opp.score_total != null ? `${opp.score_total}/10` : '—'}
                </div>
              </div>

              {description && (
                <div className="opp-desc">
                  {description.length > 220 ? description.slice(0, 220) + '…' : description}
                </div>
              )}

              <div className="opp-meta">
                {opp.market_window && (
                  <span className="tag tag-window">{WINDOW_LABEL[opp.market_window] ?? opp.market_window}</span>
                )}
                {opp.capital_type && (
                  <span className="tag tag-capital">{opp.capital_type}</span>
                )}
              </div>

              <div className="opp-bottom">
                <div className="opp-amount">{formatAmount(opp)}</div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
