import Link from 'next/link'

interface Opportunity {
  id: string
  title: string
  score_total: number | null
  decision: string | null
  urgency: string | null
  deadline: string | null
  target_contact_date: string | null
  source_name: string | null
  url_rfp: string | null
  market_window: string | null
  amount_min_cop: number | null
  amount_max_cop: number | null
  org_email: string | null
  org_email_verified: boolean
  ceo_name: string | null
  ceo_email_verified: boolean
  status: string | null
}

interface OpportunityList {
  items: Opportunity[]
  total: number
}

async function fetchOpps(filters: Record<string, string>): Promise<OpportunityList> {
  try {
    const params = new URLSearchParams({ size: '50', ...filters })
    const res = await fetch(`${process.env.API_URL}/api/v1/opportunities?${params}`, { cache: 'no-store' })
    if (!res.ok) return { items: [], total: 0 }
    return res.json()
  } catch { return { items: [], total: 0 } }
}

function decodeHtml(s: string): string {
  return s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;|&rsquo;/g, '’')
    .replace(/&nbsp;/g, ' ')
}

function daysToDeadline(deadline: string | null): number | null {
  if (!deadline) return null
  return Math.ceil((new Date(deadline).getTime() - Date.now()) / 86_400_000)
}

function formatCOP(min: number | null, max: number | null): string {
  const v = max ?? min
  if (!v) return ''
  if (v >= 1_000_000_000) return `COP $${(v / 1_000_000_000).toFixed(1)}B`
  if (v >= 1_000_000) return `COP $${Math.round(v / 1_000_000)}M`
  return `COP $${v.toLocaleString()}`
}

const WINDOW_LABEL: Record<string, string> = {
  funding_colombia: 'F. Colombia',
  funding_global: 'F. Global',
  strategic: 'Estratégico',
  latam: 'LATAM',
}

const DECISION_BADGE: Record<string, { cls: string; text: string }> = {
  go:      { cls: 'badge-go',   text: 'GO' },
  pending: { cls: 'badge-warn', text: 'PENDIENTE' },
  no_go:   { cls: 'badge-nogo', text: 'NO-GO' },
}

function AlertRow({ opp, daysClass }: { opp: Opportunity; daysClass: string }) {
  const days = daysToDeadline(opp.deadline)
  const dec = opp.decision ? DECISION_BADGE[opp.decision] : null
  const hasContact = opp.org_email_verified || opp.ceo_email_verified
  const monto = formatCOP(opp.amount_min_cop, opp.amount_max_cop)

  return (
    <Link
      href={`/opportunities/${opp.id}`}
      style={{
        display: 'grid',
        gridTemplateColumns: '70px 1fr auto auto auto auto',
        gap: 14,
        padding: '12px 16px',
        background: 'var(--bg2)',
        border: '1px solid var(--border)',
        borderRadius: 10,
        textDecoration: 'none',
        alignItems: 'center',
      }}
    >
      <div style={{ textAlign: 'center', flexShrink: 0 }}>
        <div className={`td-mono ${daysClass}`} style={{ fontSize: 18, fontWeight: 600 }}>
          {days !== null ? `${days}d` : '—'}
        </div>
        <div style={{ fontSize: 9, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: 2 }}>
          {opp.deadline ?? 'sin fecha'}
        </div>
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500, lineHeight: 1.3 }}>
          {decodeHtml(opp.title)}
        </div>
        <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {opp.market_window && <span>{WINDOW_LABEL[opp.market_window] ?? opp.market_window}</span>}
          {opp.source_name && <><span>·</span><span style={{ fontFamily: 'var(--mono)' }}>{opp.source_name}</span></>}
          {monto && <><span>·</span><span style={{ color: 'var(--go)', fontFamily: 'var(--mono)' }}>{monto}</span></>}
        </div>
      </div>
      {dec && <span className={`badge ${dec.cls}`}>{dec.text}</span>}
      <span className="td-go td-mono" style={{ fontSize: 14, fontWeight: 500 }}>
        {opp.score_total ?? '—'}/10
      </span>
      <span className={`badge ${hasContact ? 'badge-go' : 'badge-warn'}`} title={hasContact ? 'Tiene email verificado' : 'Pendiente Apollo.io'}>
        {hasContact ? '✓' : '⚠'}
      </span>
      <span style={{ fontSize: 11, color: 'var(--muted2)' }}>→</span>
    </Link>
  )
}

export default async function AlertasPage() {
  // 5 queries en paralelo
  const [urgent7, mid15, deadline30, goWithoutAction, contact30] = await Promise.all([
    fetchOpps({ days_to_deadline: '7', decision: 'go' }),
    fetchOpps({ days_to_deadline: '15', decision: 'go' }),
    fetchOpps({ days_to_deadline: '30', decision: 'go' }),
    fetchOpps({ decision: 'go', status: 'detected' }),
    fetchOpps({ days_to_contact: '30', decision: 'go' }),
  ])

  // Dedupe: 7d ⊂ 15d ⊂ 30d (la API filtra deadline ≤ N días)
  const urgentIds = new Set(urgent7.items.map(o => o.id))
  const mid15Only = mid15.items.filter(o => !urgentIds.has(o.id))
  const mid30Only = deadline30.items.filter(o => !urgentIds.has(o.id) && !mid15Only.some(m => m.id === o.id))

  // GO sin actuar excluyendo las que ya aparecen en deadlines
  const visibleIds = new Set([
    ...urgent7.items.map(o => o.id),
    ...mid15Only.map(o => o.id),
    ...mid30Only.map(o => o.id),
  ])
  const goPendientes = goWithoutAction.items.filter(o => !visibleIds.has(o.id)).slice(0, 5)

  const totalAlerts = urgent7.items.length + mid15Only.length + mid30Only.length

  return (
    <div className="page">
      <div className="topbar" style={{ margin: '-20px -24px 0', width: 'calc(100% + 48px)' }}>
        <div className="topbar-title">
          Alertas <span>— acción requerida</span>
        </div>
        {urgent7.items.length > 0 && (
          <span className="chip chip-nogo" style={{ animation: 'blink 2s infinite' }}>
            🚨 {urgent7.items.length} urgente{urgent7.items.length === 1 ? '' : 's'}
          </span>
        )}
        <span className="chip chip-warn">15d: {mid15Only.length}</span>
        <span className="chip chip-muted">30d: {mid30Only.length}</span>
      </div>

      {/* KPIs alertas */}
      <div className="kpi-row kpi-row-5" style={{ marginTop: 20 }}>
        <div className="kpi red">
          <div className="kpi-label">Vencen en 7 días</div>
          <div className="kpi-val red">{urgent7.items.length}</div>
          <div className="kpi-sub">Acción inmediata</div>
        </div>
        <div className="kpi warn">
          <div className="kpi-label">Vencen en 8-15 días</div>
          <div className="kpi-val warn">{mid15Only.length}</div>
          <div className="kpi-sub">Coordinar esta semana</div>
        </div>
        <div className="kpi blue">
          <div className="kpi-label">Vencen en 16-30 días</div>
          <div className="kpi-val blue">{mid30Only.length}</div>
          <div className="kpi-sub">Incluir en agenda</div>
        </div>
        <div className="kpi violet">
          <div className="kpi-label">GO sin gestionar</div>
          <div className="kpi-val violet">{goPendientes.length}</div>
          <div className="kpi-sub">Status = detected</div>
        </div>
        <div className="kpi go">
          <div className="kpi-label">Contactos en ≤30d</div>
          <div className="kpi-val go">{contact30.items.length}</div>
          <div className="kpi-sub">Próxima acción estratégica</div>
        </div>
      </div>

      {totalAlerts === 0 && goPendientes.length === 0 ? (
        <div className="empty-state">
          <strong>✓ Sin alertas activas.</strong><br />
          Todas las oportunidades GO están en seguimiento o tienen plazo amplio (&gt;30 días).
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* SECCIÓN 1: Urgente 7d */}
          {urgent7.items.length > 0 && (
            <section>
              <div className="section-hd">
                <h2 style={{ color: 'var(--nogo)' }}>
                  🚨 Urgente <em>— cierran en ≤ 7 días</em>
                </h2>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {urgent7.items.map((opp) => (
                  <AlertRow key={opp.id} opp={opp} daysClass="td-nogo" />
                ))}
              </div>
            </section>
          )}

          {/* SECCIÓN 2: 15d */}
          {mid15Only.length > 0 && (
            <section>
              <div className="section-hd">
                <h2 style={{ color: 'var(--amber)' }}>
                  ⚠ Esta semana <em>— cierran en 8-15 días</em>
                </h2>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {mid15Only.map((opp) => (
                  <AlertRow key={opp.id} opp={opp} daysClass="td-amber" />
                ))}
              </div>
            </section>
          )}

          {/* SECCIÓN 3: 30d */}
          {mid30Only.length > 0 && (
            <section>
              <div className="section-hd">
                <h2 style={{ color: 'var(--blue)' }}>
                  📅 Próximas semanas <em>— cierran en 16-30 días</em>
                </h2>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {mid30Only.map((opp) => (
                  <AlertRow key={opp.id} opp={opp} daysClass="td-muted" />
                ))}
              </div>
            </section>
          )}

          {/* SECCIÓN 4: GO sin acción */}
          {goPendientes.length > 0 && (
            <section>
              <div className="section-hd">
                <h2 style={{ color: 'var(--violet)' }}>
                  ▱ GO sin gestionar <em>— oportunidades detectadas sin asignar</em>
                </h2>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {goPendientes.map((opp) => (
                  <AlertRow key={opp.id} opp={opp} daysClass="td-muted" />
                ))}
              </div>
            </section>
          )}

          {/* SECCIÓN 5: Contactos estratégicos próximos */}
          {contact30.items.length > 0 && (
            <section>
              <div className="section-hd">
                <h2 style={{ color: 'var(--go)' }}>
                  ▶ Próximos contactos estratégicos <em>— próximas acciones esperadas (≤30 días)</em>
                </h2>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {contact30.items.map((opp) => {
                  const days = opp.target_contact_date
                    ? Math.ceil((new Date(opp.target_contact_date).getTime() - Date.now()) / 86_400_000)
                    : null
                  const daysClass = days !== null && days <= 7 ? 'td-nogo' : days !== null && days <= 15 ? 'td-amber' : 'td-muted'
                  return (
                    <Link
                      key={`contact-${opp.id}`}
                      href={`/opportunities/${opp.id}`}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '70px 1fr auto auto auto auto',
                        gap: 14,
                        padding: '12px 16px',
                        background: 'var(--bg2)',
                        border: '1px solid var(--go-bdr)',
                        borderRadius: 10,
                        textDecoration: 'none',
                        alignItems: 'center',
                      }}
                    >
                      <div style={{ textAlign: 'center', flexShrink: 0 }}>
                        <div className={`td-mono ${daysClass}`} style={{ fontSize: 18, fontWeight: 600 }}>
                          {days !== null ? `${days}d` : '—'}
                        </div>
                        <div style={{ fontSize: 9, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: 2 }}>
                          contactar
                        </div>
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500, lineHeight: 1.3 }}>
                          {decodeHtml(opp.title)}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                          Target: {opp.target_contact_date} · {opp.source_name}
                        </div>
                      </div>
                      <span className="badge badge-go">GO</span>
                      <span className="td-go td-mono" style={{ fontSize: 14, fontWeight: 500 }}>
                        {opp.score_total ?? '—'}/10
                      </span>
                      <span className={`badge ${opp.org_email_verified || opp.ceo_email_verified ? 'badge-go' : 'badge-warn'}`}>
                        {opp.org_email_verified || opp.ceo_email_verified ? '✓' : '⚠'}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--muted2)' }}>→</span>
                    </Link>
                  )
                })}
              </div>
            </section>
          )}

        </div>
      )}

      <div style={{ marginTop: 24, padding: '12px 16px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r)', fontSize: 11, color: 'var(--muted)', lineHeight: 1.6 }}>
        💡 <strong style={{ color: 'var(--muted2)' }}>Sprint S4</strong> — n8n enviará estas alertas vía Slack/email automáticamente cada mañana a las 9am.
      </div>
    </div>
  )
}
