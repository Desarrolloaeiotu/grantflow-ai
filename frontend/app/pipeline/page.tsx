interface Opportunity {
  id: string
  title: string
  score_total: number | null
  decision: string | null
  urgency: string | null
  deadline: string | null
  source_name: string | null
  url_rfp: string | null
  market_window: string | null
  amount_min_cop: number | null
  amount_max_cop: number | null
  org_email_verified: boolean
  ceo_email_verified: boolean
}

async function getGoOpportunities(): Promise<Opportunity[]> {
  try {
    const res = await fetch(
      `${process.env.API_URL}/api/v1/opportunities?decision=go&size=50`,
      { cache: 'no-store' }
    )
    if (!res.ok) return []
    const data = await res.json()
    return data.items ?? []
  } catch {
    return []
  }
}

const WINDOW_LABELS: Record<string, string> = {
  funding_colombia: 'F. Colombia',
  funding_global:   'F. Global',
  strategic:        'Estratégico',
  latam:            'LATAM',
}

function formatCOP(n: number | null): string {
  if (!n) return '—'
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`
  if (n >= 1_000_000) return `$${Math.round(n / 1_000_000)}M`
  return `$${n.toLocaleString()}`
}

function daysLabel(deadline: string | null): { text: string; cls: string } {
  if (!deadline) return { text: '—', cls: '' }
  const days = Math.ceil((new Date(deadline).getTime() - Date.now()) / 86_400_000)
  if (days < 0)  return { text: 'Vencida', cls: 'td-nogo' }
  if (days <= 7) return { text: `${days}d`, cls: 'td-nogo' }
  if (days <= 30) return { text: `${days}d`, cls: 'td-amber' }
  return { text: `${days}d`, cls: 'td-muted' }
}

export default async function PipelinePage() {
  const opportunities = await getGoOpportunities()
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  // Stats
  const withVerifiedEmail = opportunities.filter(o => o.org_email_verified || o.ceo_email_verified).length
  const urgent = opportunities.filter(o => o.urgency === 'high').length
  const scoreEqual8Plus = opportunities.filter(o => (o.score_total ?? 0) >= 8).length

  // Alerts: opps que vencen en ≤7 días (basado en deadline)
  const alertsUrgent = opportunities.filter((o) => {
    if (!o.deadline) return false
    const days = Math.ceil((new Date(o.deadline).getTime() - Date.now()) / 86_400_000)
    return days >= 0 && days <= 7
  })

  return (
    <div className="page">

      <div className="topbar" style={{ margin: '-20px -24px 0', width: 'calc(100% + 48px)' }}>
        <div className="topbar-title">
          Pipeline <span>— oportunidades GO priorizadas</span>
        </div>
        <span className="chip chip-go">GO: {opportunities.length}</span>
        <span className="chip chip-warn">Urgentes: {urgent}</span>
        <span className="chip chip-muted">Score ≥8: {scoreEqual8Plus}</span>
      </div>

      {/* Banner de alertas urgentes */}
      {alertsUrgent.length > 0 && (
        <div style={{
          marginTop: 20,
          padding: '14px 18px',
          background: 'var(--nogo-bg)',
          border: '1px solid rgba(248,113,113,0.4)',
          borderRadius: 'var(--r-lg)',
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}>
          <span style={{ fontSize: 22, animation: 'blink 2s infinite' }}>🚨</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--nogo)', marginBottom: 4 }}>
              {alertsUrgent.length} oportunidad{alertsUrgent.length === 1 ? '' : 'es'} GO con cierre ≤ 7 días
            </div>
            <div style={{ fontSize: 11, color: 'var(--muted2)', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {alertsUrgent.slice(0, 3).map((o) => {
                const days = Math.ceil((new Date(o.deadline!).getTime() - Date.now()) / 86_400_000)
                return (
                  <a key={o.id} href={`/opportunities/${o.id}`} style={{ color: 'var(--nogo)', textDecoration: 'underline', textDecorationColor: 'rgba(248,113,113,0.3)' }}>
                    {o.title.slice(0, 50)}{o.title.length > 50 ? '…' : ''} ({days}d)
                  </a>
                )
              })}
              {alertsUrgent.length > 3 && <span>+ {alertsUrgent.length - 3} más</span>}
            </div>
          </div>
          <a href="/alertas" className="link-btn" style={{ color: 'var(--nogo)', borderColor: 'rgba(248,113,113,0.3)' }}>
            → Ver alertas completas
          </a>
        </div>
      )}

      {/* Export options panel */}
      {opportunities.length > 0 && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--go-bdr)', borderRadius: 'var(--r-lg)', padding: 18, marginTop: 20 }}>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 10 }}>
            Exportar al CRM
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted2)', lineHeight: 1.6, marginBottom: 14 }}>
            El CSV incluye: ID, título, descripción, decisión, score, urgencia, ventana, capital, financiador, montos (raw y formateados), deadline,
            URLs (RFP + source), <strong style={{ color: 'var(--text)' }}>website y email de organización (verificado Apollo)</strong>,
            <strong style={{ color: 'var(--text)' }}> nombre, cargo, email y LinkedIn del CEO</strong>, scoring breakdown C1-C5, justificación LLM y estado.
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            <a
              href={`${apiUrl}/api/v1/opportunities/export?decision=go`}
              className="link-btn primary"
              style={{ justifyContent: 'center', padding: '10px 14px' }}
            >
              ↓ Todas las GO ({opportunities.length})
            </a>
            <a
              href={`${apiUrl}/api/v1/opportunities/export?decision=go&min_score=8`}
              className="link-btn"
              style={{ justifyContent: 'center', padding: '10px 14px' }}
            >
              ↓ Score ≥ 8 ({scoreEqual8Plus})
            </a>
            <a
              href={`${apiUrl}/api/v1/opportunities/export?decision=go&verified_only=true`}
              className="link-btn"
              style={{ justifyContent: 'center', padding: '10px 14px' }}
            >
              ↓ Solo verificados ({withVerifiedEmail})
            </a>
            <a
              href={`${apiUrl}/api/v1/opportunities/export?decision=`}
              className="link-btn"
              style={{ justifyContent: 'center', padding: '10px 14px', color: 'var(--muted2)' }}
            >
              ↓ Todas (377)
            </a>
          </div>
        </div>
      )}

      <div className="section-hd">
        <h2>
          Oportunidades GO <em>— {opportunities.length} listas para gestión</em>
        </h2>
      </div>

      {opportunities.length === 0 ? (
        <div className="empty-state">
          <strong>Sin oportunidades GO todavía.</strong><br />
          Ejecuta los scrapers + rescore para iniciar el pipeline.
        </div>
      ) : (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Oportunidad</th>
                <th>Ventana</th>
                <th>Monto COP</th>
                <th>Score</th>
                <th>Urgencia</th>
                <th>Cierre</th>
                <th>Contactos</th>
                <th>Fuente</th>
              </tr>
            </thead>
            <tbody>
              {opportunities.map((opp) => {
                const dl = daysLabel(opp.deadline)
                const hasVerified = opp.org_email_verified || opp.ceo_email_verified
                return (
                  <tr key={opp.id}>
                    <td style={{ maxWidth: 320 }}>
                      <a href={`/opportunities/${opp.id}`} className="td-link" style={{ fontWeight: 500, fontSize: 12.5 }}>
                        {opp.title}
                      </a>
                    </td>
                    <td>
                      {opp.market_window && (
                        <span className="badge badge-violet">
                          {WINDOW_LABELS[opp.market_window] ?? opp.market_window}
                        </span>
                      )}
                    </td>
                    <td className="td-go td-mono">
                      {opp.amount_min_cop || opp.amount_max_cop ? (
                        <>
                          {formatCOP(opp.amount_min_cop)}
                          {opp.amount_max_cop && opp.amount_min_cop !== opp.amount_max_cop
                            ? ` — ${formatCOP(opp.amount_max_cop)}`
                            : ''}
                        </>
                      ) : (
                        <span style={{ color: 'var(--muted)' }}>—</span>
                      )}
                    </td>
                    <td className="td-go td-mono" style={{ fontSize: 14, fontWeight: 500 }}>
                      {opp.score_total ?? '—'}
                    </td>
                    <td>
                      {opp.urgency && (
                        <span className={`badge ${opp.urgency === 'high' ? 'badge-nogo' : opp.urgency === 'medium' ? 'badge-warn' : 'badge-muted'}`}>
                          {opp.urgency === 'high' ? 'Urgente' : opp.urgency === 'medium' ? 'Media' : 'Baja'}
                        </span>
                      )}
                    </td>
                    <td className={`td-mono ${dl.cls}`}>{dl.text}</td>
                    <td>
                      {hasVerified ? (
                        <span className="badge badge-go">✓ Verificado</span>
                      ) : (
                        <span className="badge badge-warn">⚠ Apollo S5</span>
                      )}
                    </td>
                    <td className="td-muted" style={{ fontSize: 11 }}>{opp.source_name ?? '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
