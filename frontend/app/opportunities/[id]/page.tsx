import { Fragment } from 'react'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import OpportunityActions from './OpportunityActions'

interface OpportunityDetail {
  id: string
  title: string
  description: string | null
  funder_id: string | null
  amount_min_cop: number | null
  amount_max_cop: number | null
  deadline: string | null
  target_contact_date: string | null
  url_rfp: string | null
  url_source: string | null
  source_name: string | null
  org_website: string | null
  org_email: string | null
  org_email_verified: boolean
  ceo_name: string | null
  ceo_title: string | null
  ceo_email: string | null
  ceo_email_verified: boolean
  ceo_linkedin_url: string | null
  market_window: string | null
  capital_type: string | null
  score_total: number | null
  score_details: {
    c1?: number; c2?: number; c3?: number; c4?: number; c5?: number
    llm_justification?: string
    confidence?: string
  } | null
  decision: string | null
  urgency: string | null
  status: string | null
  detected_at: string | null
}

interface OpportunityListItem {
  id: string
  title: string
  score_total: number | null
  decision: string | null
  source_name: string | null
  deadline: string | null
}

async function getOpp(id: string): Promise<OpportunityDetail | null> {
  try {
    const res = await fetch(`${process.env.API_URL}/api/v1/opportunities/${id}`, { cache: 'no-store' })
    if (!res.ok) return null
    return res.json()
  } catch { return null }
}

async function getRelated(source: string | null, opportunityId: string): Promise<OpportunityListItem[]> {
  if (!source) return []
  try {
    const params = new URLSearchParams({ size: '5', source })
    const res = await fetch(`${process.env.API_URL}/api/v1/opportunities?${params}`, { cache: 'no-store' })
    if (!res.ok) return []
    const data = await res.json()
    return (data.items ?? []).filter((o: OpportunityListItem) => o.id !== opportunityId).slice(0, 4)
  } catch { return [] }
}

const CRITERIA_LABELS = [
  'Alineación estratégica',
  'Ajuste del modelo',
  'Coherencia del ticket',
  'Viabilidad operativa',
  'Potencial relacional',
]

const WINDOW_LABELS: Record<string, string> = {
  funding_colombia: 'Funding Colombia',
  funding_global: 'Funding Global',
  strategic: 'Estratégico',
  latam: 'LATAM',
}

const DECISION_BADGE: Record<string, { cls: string; text: string }> = {
  go:      { cls: 'badge-go',   text: 'GO' },
  pending: { cls: 'badge-warn', text: 'PENDIENTE' },
  no_go:   { cls: 'badge-nogo', text: 'NO-GO' },
}

function formatCOP(n: number | null): string {
  if (!n) return '—'
  if (n >= 1_000_000_000) return `COP $${(n / 1_000_000_000).toFixed(2)}B`
  if (n >= 1_000_000) return `COP $${Math.round(n / 1_000_000)}M`
  return `COP $${n.toLocaleString()}`
}

function daysLeft(deadline: string | null): { days: number | null; text: string; color: string } {
  if (!deadline) return { days: null, text: 'Sin fecha de cierre', color: 'var(--muted)' }
  const days = Math.ceil((new Date(deadline).getTime() - Date.now()) / 86_400_000)
  if (days < 0)  return { days, text: `Vencida hace ${-days} días`, color: 'var(--nogo)' }
  if (days <= 7) return { days, text: `Cierra en ${days} días`,    color: 'var(--nogo)' }
  if (days <= 30) return { days, text: `Cierra en ${days} días`,   color: 'var(--amber)' }
  return { days, text: `Cierra en ${days} días`, color: 'var(--muted2)' }
}

function decodeHtml(s: string): string {
  return s
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;|&rsquo;/g, '’')
    .replace(/&lsquo;/g, '‘').replace(/&ldquo;/g, '“').replace(/&rdquo;/g, '”')
    .replace(/&nbsp;/g, ' ')
}

interface TreatmentStep {
  step: number
  text: string
  icon: string
  priority: 'urgent' | 'normal' | 'note'
}

function generateTreatment(opp: OpportunityDetail): TreatmentStep[] {
  const steps: TreatmentStep[] = []
  const dl = daysLeft(opp.deadline)
  const score = opp.score_total ?? 0

  // Paso 1: tiempo
  if (dl.days !== null && dl.days < 0) {
    steps.push({ step: 1, text: 'Oportunidad vencida — archivar o investigar próximas ediciones del programa.', icon: '⏵', priority: 'note' })
  } else if (dl.days !== null && dl.days <= 7) {
    steps.push({ step: 1, text: 'Cierre inmediato — coordinar respuesta hoy mismo, asignar responsable de Alianzas en las próximas 24h.', icon: '⚡', priority: 'urgent' })
  } else if (dl.days !== null && dl.days <= 30) {
    steps.push({ step: 1, text: 'Plazo medio — incluir en agenda semanal del equipo. Borrador de carta de intención esta semana.', icon: '⏱', priority: 'normal' })
  } else {
    steps.push({ step: 1, text: 'Plazo amplio — incluir en planificación trimestral. Investigar antecedentes del financiador.', icon: '📅', priority: 'normal' })
  }

  // Paso 2: scoring + decisión
  if (score >= 8) {
    steps.push({ step: 2, text: 'Score alto (≥8) — máxima prioridad. Activar equipo: técnico + alianzas + dirección.', icon: '★', priority: 'urgent' })
  } else if (score >= 6) {
    steps.push({ step: 2, text: 'Score viable (6-7) — pasar a revisión humana. Validar ajuste con dirección de Alianzas.', icon: '✓', priority: 'normal' })
  } else if (score >= 4) {
    steps.push({ step: 2, text: 'Score medio (4-5) — revisar manualmente. Alineación parcial detectada por LLM.', icon: '?', priority: 'normal' })
  } else if (score > 0) {
    steps.push({ step: 2, text: 'Score bajo — no perseguir activamente. Posible archivo o reasignar a otra área.', icon: '↓', priority: 'note' })
  } else {
    steps.push({ step: 2, text: 'Sin scoring LLM aún — correr `app.scrapers.rescore` para evaluar alineación.', icon: '⚠', priority: 'note' })
  }

  // Paso 3: contacto
  if (opp.ceo_email && opp.ceo_email_verified) {
    steps.push({ step: 3, text: `Email del CEO verificado (${opp.ceo_email}) — enviar carta de intención directa con brief aeioTU.`, icon: '✉', priority: 'normal' })
  } else if (opp.ceo_email) {
    steps.push({ step: 3, text: 'CEO identificado pero email NO verificado — pasar por Apollo.io antes de contactar (Sprint S5).', icon: '⚠', priority: 'note' })
  } else if (opp.org_email) {
    steps.push({ step: 3, text: 'Usar email institucional de la organización para primer contacto. Pedir referencia al CEO/programa officer.', icon: '✉', priority: 'normal' })
  } else {
    steps.push({ step: 3, text: 'Sin contacto recolectado — buscar en LinkedIn de la organización + Apollo.io (Sprint S5).', icon: '?', priority: 'note' })
  }

  // Paso 4: ticket
  if (opp.amount_max_cop && opp.amount_max_cop >= 400_000_000) {
    if (opp.amount_max_cop >= 1_000_000_000) {
      steps.push({ step: 4, text: 'Ticket grande (≥$1B COP) — preparar propuesta completa con equipo técnico + financiero.', icon: '$', priority: 'urgent' })
    } else {
      steps.push({ step: 4, text: 'Ticket viable (≥$400M COP, dentro del rango aeioTU) — propuesta estándar.', icon: '$', priority: 'normal' })
    }
  } else if (opp.amount_max_cop) {
    steps.push({ step: 4, text: `Ticket pequeño (${formatCOP(opp.amount_max_cop)}) — considerar como piloto o quickwin para abrir relación.`, icon: '$', priority: 'note' })
  } else {
    steps.push({ step: 4, text: 'Monto no especificado — consultar al financiador o documentos de la convocatoria.', icon: '?', priority: 'note' })
  }

  return steps
}

export default async function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const opp = await getOpp(id)
  if (!opp) notFound()

  const related = await getRelated(opp.source_name, id)
  const dl = daysLeft(opp.deadline)
  const dec = opp.decision ? DECISION_BADGE[opp.decision] : null
  const sd = opp.score_details ?? {}
  const criteria = [sd.c1, sd.c2, sd.c3, sd.c4, sd.c5]
  const title = decodeHtml(opp.title)
  const description = opp.description ? decodeHtml(opp.description) : null
  const treatment = generateTreatment(opp)
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  return (
    <div className="page">
      {/* Topbar */}
      <div className="topbar" style={{ margin: '-20px -24px 0', width: 'calc(100% + 48px)' }}>
        <div className="topbar-title" style={{ fontSize: 16 }}>
          <Link href="/" style={{ color: 'var(--muted)', marginRight: 8 }}>← Oportunidades</Link>
          <span>· detalle</span>
        </div>
        {dec && <span className={`chip chip-${opp.decision === 'go' ? 'go' : opp.decision === 'pending' ? 'warn' : 'nogo'}`}>{dec.text}</span>}
        {opp.score_total != null && (
          <span className="chip chip-go">Score {opp.score_total}/10</span>
        )}
        {dl.days !== null && dl.days <= 7 && dl.days >= 0 && (
          <span className="chip chip-nogo" style={{ animation: 'blink 2s infinite' }}>⏱ {dl.days}d</span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginTop: 20, alignItems: 'start' }}>

        {/* ── Columna principal ─────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Header con título */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 22, borderLeft: `3px solid ${opp.decision === 'go' ? 'var(--go)' : opp.decision === 'pending' ? 'var(--amber)' : 'var(--border2)'}` }}>
            <h1 style={{ fontFamily: 'var(--serif)', fontSize: 22, lineHeight: 1.3, color: 'var(--text)', marginBottom: 14, fontWeight: 400 }}>
              {title}
            </h1>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
              {opp.market_window && (
                <span className="tag tag-window">{WINDOW_LABELS[opp.market_window] ?? opp.market_window}</span>
              )}
              {opp.capital_type && (
                <span className="tag tag-capital">{opp.capital_type}</span>
              )}
              {opp.source_name && (
                <span className="tag tag-source">{opp.source_name}</span>
              )}
              {opp.urgency === 'high' && <span className="tag tag-urgent">URGENTE</span>}
              {opp.urgency === 'medium' && <span className="tag tag-med">MEDIA</span>}
            </div>

            {description && (
              <div style={{ fontSize: 13, color: 'var(--muted2)', lineHeight: 1.7, padding: '10px 14px', borderLeft: '2px solid var(--border2)', background: 'var(--bg3)', borderRadius: 6 }}>
                {description}
              </div>
            )}
          </div>

          {/* Cómo tratar */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>
              ¿Cómo tratar esta oportunidad?
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {treatment.map((t) => {
                const color = t.priority === 'urgent' ? 'var(--nogo)' : t.priority === 'normal' ? 'var(--go)' : 'var(--muted2)'
                const bg = t.priority === 'urgent' ? 'var(--nogo-bg)' : t.priority === 'normal' ? 'var(--go-bg)' : 'var(--bg3)'
                return (
                  <div key={t.step} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 10px', background: bg, borderRadius: 6, border: `1px solid ${color}30` }}>
                    <span style={{ width: 22, height: 22, borderRadius: '50%', background: 'var(--bg4)', color, fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontFamily: 'var(--mono)' }}>
                      {t.step}
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.5, flex: 1 }}>
                      <span style={{ marginRight: 6 }}>{t.icon}</span>
                      {t.text}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Acciones CRM (Client Component) */}
          <OpportunityActions opportunityId={opp.id} initialStatus={opp.status} apiUrl={apiUrl} />

          {/* Acciones / enlaces externos */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 10 }}>
              Enlaces externos
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {opp.url_rfp && (
                <a href={opp.url_rfp} target="_blank" rel="noopener noreferrer" className="link-btn primary">
                  → Ver convocatoria
                </a>
              )}
              {opp.org_website && (
                <a href={opp.org_website} target="_blank" rel="noopener noreferrer" className="link-btn">
                  ⌘ Sitio organización
                </a>
              )}
              {opp.ceo_email && (
                <a
                  href={`mailto:${opp.ceo_email}?subject=${encodeURIComponent('Oportunidad ' + title + ' - aeioTU')}`}
                  className="link-btn"
                  style={!opp.ceo_email_verified ? { color: 'var(--amber)', borderColor: 'rgba(251,191,36,0.3)' } : {}}
                >
                  {opp.ceo_email_verified ? '✉ Contactar CEO' : '⚠ CEO (sin verificar)'}
                </a>
              )}
              {opp.org_email && (
                <a href={`mailto:${opp.org_email}`} className="link-btn">
                  ✉ Email institucional
                </a>
              )}
              {opp.ceo_linkedin_url && (
                <a href={opp.ceo_linkedin_url} target="_blank" rel="noopener noreferrer" className="link-btn" style={{ color: '#0A66C2', borderColor: 'rgba(10,102,194,0.3)' }}>
                  <span style={{ fontWeight: 700 }}>in</span> LinkedIn CEO
                </a>
              )}
            </div>
          </div>

          {/* Scoring detallado */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 14 }}>
              Scoring por criterio
            </div>

            {opp.score_total == null ? (
              <div style={{ color: 'var(--muted)', fontSize: 12 }}>
                Esta oportunidad aún no ha sido evaluada por el LLM. Corre <code style={{ fontFamily: 'var(--mono)', color: 'var(--amber)' }}>app.scrapers.rescore</code> para puntuarla.
              </div>
            ) : (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '8px 16px', alignItems: 'center', marginBottom: 14 }}>
                  {CRITERIA_LABELS.map((label, i) => {
                    const pts = criteria[i] ?? 0
                    const color = pts === 2 ? 'var(--go)' : pts === 1 ? 'var(--amber)' : 'var(--muted)'
                    return (
                      <Fragment key={i}>
                        <span style={{ fontSize: 12, color: 'var(--muted2)' }}>
                          C{i + 1} · {label}
                        </span>
                        <span style={{ fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 500, color, textAlign: 'right' }}>
                          {pts}/2
                        </span>
                      </Fragment>
                    )
                  })}
                </div>

                <div style={{ height: 4, background: 'var(--bg4)', borderRadius: 2, overflow: 'hidden', marginBottom: 14 }}>
                  <div style={{
                    height: '100%',
                    width: `${(opp.score_total / 10) * 100}%`,
                    background: opp.decision === 'go' ? 'linear-gradient(90deg, var(--go), #06D6A0)' : opp.decision === 'pending' ? 'linear-gradient(90deg, var(--amber), #F59E0B)' : 'var(--nogo)',
                  }} />
                </div>

                {sd.llm_justification
                  && !sd.llm_justification.startsWith('LLM error')
                  && !sd.llm_justification.startsWith('LLM scoring not available')
                  && !sd.llm_justification.includes('no API key')
                  && (
                  <div style={{ background: 'var(--go-bg)', border: '1px solid var(--go-bdr)', borderRadius: 8, padding: '10px 12px', fontSize: 12, color: 'var(--go)', lineHeight: 1.6, fontStyle: 'italic' }}>
                    "{sd.llm_justification}"
                    {sd.confidence && <div style={{ fontStyle: 'normal', color: 'var(--muted)', fontSize: 10, marginTop: 6 }}>Confianza LLM: {sd.confidence}</div>}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Oportunidades relacionadas */}
          {related.length > 0 && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>
                Otras de {opp.source_name}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {related.map((r) => {
                  const rdec = r.decision ? DECISION_BADGE[r.decision] : null
                  return (
                    <Link
                      key={r.id}
                      href={`/opportunities/${r.id}`}
                      style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center', padding: '10px 12px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, textDecoration: 'none' }}
                    >
                      <span style={{ color: 'var(--text)', fontSize: 12.5, fontWeight: 500, flex: 1, lineHeight: 1.4 }}>
                        {decodeHtml(r.title).slice(0, 80)}{r.title.length > 80 ? '…' : ''}
                      </span>
                      <span style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
                        {rdec && <span className={`badge ${rdec.cls}`}>{rdec.text}</span>}
                        {r.score_total != null && (
                          <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--go)', fontWeight: 500 }}>
                            {r.score_total}/10
                          </span>
                        )}
                      </span>
                    </Link>
                  )
                })}
              </div>
            </div>
          )}

        </div>

        {/* ── Columna derecha (rail) ─────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, position: 'sticky', top: 20 }}>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              Monto
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 18, color: 'var(--go)', fontWeight: 500 }}>
              {opp.amount_min_cop || opp.amount_max_cop
                ? formatCOP(opp.amount_max_cop ?? opp.amount_min_cop)
                : 'Sin información'}
            </div>
            {opp.amount_min_cop && opp.amount_max_cop && opp.amount_min_cop !== opp.amount_max_cop && (
              <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                Min: {formatCOP(opp.amount_min_cop)}
              </div>
            )}
          </div>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              Fecha de cierre
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 14, color: dl.color, fontWeight: 500 }}>
              {opp.deadline ?? 'Sin fecha'}
            </div>
            <div style={{ fontSize: 11, color: dl.color, marginTop: 4 }}>
              {dl.text}
            </div>
          </div>

          {opp.target_contact_date && (() => {
            const days = Math.ceil((new Date(opp.target_contact_date).getTime() - Date.now()) / 86_400_000)
            const color = days < 0 ? 'var(--nogo)' : days <= 7 ? 'var(--nogo)' : days <= 30 ? 'var(--amber)' : 'var(--muted2)'
            const status = days < 0 ? `Vencido hace ${-days} días` : days === 0 ? 'Contactar HOY' : `Contactar en ${days} días`
            return (
              <div style={{ background: 'var(--bg2)', border: `1px solid ${color}40`, borderRadius: 'var(--r-lg)', padding: 16, borderLeft: `3px solid ${color}` }}>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
                  Próximo contacto estratégico
                </div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 14, color, fontWeight: 500 }}>
                  📞 {opp.target_contact_date}
                </div>
                <div style={{ fontSize: 11, color, marginTop: 4 }}>
                  {status}
                </div>
                <div style={{ fontSize: 9.5, color: 'var(--muted)', marginTop: 6, lineHeight: 1.4 }}>
                  Ventana óptima de contacto / negociación (independiente del deadline del programa)
                </div>
              </div>
            )
          })()}

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              Organización
            </div>
            {opp.org_website && (
              <a href={opp.org_website} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--blue)', fontSize: 12, fontFamily: 'var(--mono)', display: 'block', marginBottom: 6 }}>
                {opp.org_website.replace(/^https?:\/\//, '')} →
              </a>
            )}
            {opp.org_email ? (
              <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--blue)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: opp.org_email_verified ? 'var(--go)' : 'var(--amber)' }}></span>
                {opp.org_email}
              </div>
            ) : (
              <div style={{ fontSize: 11, color: 'var(--muted)', fontStyle: 'italic' }}>
                Sin email · Apollo.io S5
              </div>
            )}
          </div>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              CEO / Representante
            </div>
            {opp.ceo_name ? (
              <>
                <div style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500, marginBottom: 2 }}>
                  {opp.ceo_name}
                </div>
                {opp.ceo_title && (
                  <div style={{ fontSize: 11, color: 'var(--muted2)', marginBottom: 6 }}>
                    {opp.ceo_title}
                  </div>
                )}
                {opp.ceo_email && (
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--blue)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: opp.ceo_email_verified ? 'var(--go)' : 'var(--amber)' }}></span>
                    {opp.ceo_email}
                  </div>
                )}
                {opp.ceo_linkedin_url && (
                  <a href={opp.ceo_linkedin_url} target="_blank" rel="noopener noreferrer" style={{ color: '#0A66C2', fontSize: 11, fontFamily: 'var(--mono)' }}>
                    {opp.ceo_linkedin_url.replace(/^https?:\/\//, '')} →
                  </a>
                )}
              </>
            ) : (
              <div style={{ fontSize: 11.5, color: 'var(--muted)', fontStyle: 'italic', lineHeight: 1.5 }}>
                ⚠ Sin contacto<br />
                <span style={{ fontSize: 10 }}>Pendiente Apollo.io (Sprint S5)</span>
              </div>
            )}
          </div>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              Metadata
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5, fontSize: 11 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Status</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)' }}>{opp.status ?? 'detected'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Decisión</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)' }}>{opp.decision ?? '—'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Urgencia</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)' }}>{opp.urgency ?? '—'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Fuente</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)', fontSize: 10 }}>{opp.source_name ?? '—'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Detectada</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)', fontSize: 10 }}>
                  {opp.detected_at ? new Date(opp.detected_at).toLocaleDateString('es-CO') : '—'}
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
