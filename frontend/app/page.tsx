import Link from 'next/link'
import SearchBar from './components/SearchBar'
import ScraperControls from './components/ScraperControls'

interface Opportunity {
  id: string
  title: string
  description: string | null
  score_total: number | null
  decision: string | null
  urgency: string | null
  deadline: string | null
  source_name: string | null
  url_rfp: string | null
  org_website: string | null
  org_email: string | null
  org_email_verified: boolean
  ceo_name: string | null
  ceo_title?: string | null
  ceo_email: string | null
  ceo_email_verified: boolean
  ceo_linkedin_url: string | null
  market_window: string | null
  capital_type: string | null
  amount_min_cop: number | null
  amount_max_cop: number | null
  score_details: {
    c1?: number; c2?: number; c3?: number; c4?: number; c5?: number
    llm_justification?: string
    confidence?: string
  } | null
}

interface OpportunityList {
  items: Opportunity[]
  total: number
  page: number
  size: number
}

interface Metrics {
  total_detected: number
  total_go: number
  total_pending: number
  total_no_go: number
}

async function getMetrics(): Promise<Metrics | null> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboard/metrics`, { cache: 'no-store' })
    if (!res.ok) return null
    return res.json()
  } catch { return null }
}

async function getOpportunities(filters: Record<string, string>, page = 1): Promise<OpportunityList | null> {
  try {
    const params = new URLSearchParams({ size: '12', page: String(page) })
    for (const [k, v] of Object.entries(filters)) {
      if (v && v !== 'all') params.set(k, v)
    }
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/opportunities?${params}`, { cache: 'no-store' })
    if (!res.ok) return null
    return res.json()
  } catch { return null }
}

// Highlight de coincidencias de búsqueda
function highlight(text: string, q?: string): React.ReactNode {
  if (!q) return text
  const re = new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  const parts = text.split(re)
  return parts.map((p, i) =>
    p.toLowerCase() === q.toLowerCase()
      ? <mark key={i} style={{ background: 'rgba(251,191,36,0.3)', color: 'var(--amber)', padding: '0 2px', borderRadius: 2 }}>{p}</mark>
      : <span key={i}>{p}</span>
  )
}

const DECISION_FILTERS = [
  { key: 'all',     label: 'Todas' },
  { key: 'go',      label: 'GO' },
  { key: 'pending', label: 'Pendiente' },
  { key: 'no_go',   label: 'No-Go' },
]

const WINDOW_FILTERS = [
  { key: 'funding_global',   label: 'Funding Global' },
  { key: 'funding_colombia', label: 'Funding Colombia' },
  { key: 'latam',            label: 'LATAM' },
  { key: 'strategic',        label: 'Estratégico' },
]

const URGENCY_FILTERS = [
  { key: 'high',   label: 'Urgente' },
  { key: 'medium', label: 'Media' },
]

const WINDOW_LABEL: Record<string, string> = {
  funding_colombia: 'Funding Colombia',
  funding_global: 'Funding Global',
  strategic: 'Estratégico',
  latam: 'LATAM',
}

function decodeHtml(s: string): string {
  return s
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&rsquo;/g, '’')
    .replace(/&lsquo;/g, '‘')
    .replace(/&ldquo;/g, '“')
    .replace(/&rdquo;/g, '”')
    .replace(/&nbsp;/g, ' ')
}

function daysLabel(deadline: string | null): { text: string; cls: string; chipText: string } {
  if (!deadline) return { text: 'Sin cierre', cls: '', chipText: '—' }
  const days = Math.ceil((new Date(deadline).getTime() - Date.now()) / 86_400_000)
  if (days < 0)  return { text: `Vencida hace ${-days}d`, cls: 'deadline-urgent', chipText: 'VENCIDA' }
  if (days <= 7) return { text: `Cierra en ${days}d`,    cls: 'deadline-urgent', chipText: `${days}D` }
  if (days <= 30) return { text: `Cierra en ${days}d`,   cls: 'deadline-med',    chipText: `${days}D` }
  return { text: `Cierra en ${days}d`, cls: '', chipText: `${days}D` }
}

function formatAmount(opp: Opportunity): string {
  const v = opp.amount_max_cop ?? opp.amount_min_cop
  if (!v) return 'Monto no especificado'
  if (v >= 1_000_000_000) return `COP $${(v / 1_000_000_000).toFixed(2)}B`
  if (v >= 1_000_000) return `COP $${Math.round(v / 1_000_000)}M`
  return `COP $${v.toLocaleString()}`
}

function scoreCircleCls(score: number | null, decision: string | null): string {
  if (decision === 'go') return 'sc-go'
  if (decision === 'pending') return 'sc-warn'
  if (decision === 'no_go') return 'sc-no'
  if (score == null) return 'sc-warn'
  if (score >= 6) return 'sc-go'
  if (score >= 4) return 'sc-warn'
  return 'sc-no'
}

function cardCls(decision: string | null): string {
  if (decision === 'go') return 'go-card'
  if (decision === 'pending') return 'pend-card'
  if (decision === 'no_go') return 'nogo-card'
  return ''
}

function buildFilterUrl(current: Record<string, string>, key: string, value: string): string {
  const next = { ...current }
  if (value === 'all' || next[key] === value) {
    delete next[key] // toggle off
  } else {
    next[key] = value
  }
  const params = new URLSearchParams(next)
  const qs = params.toString()
  return qs ? `/?${qs}` : '/'
}

export default async function OpportunitiesPage({
  searchParams,
}: {
  searchParams: Promise<{ decision?: string; window?: string; urgency?: string; score_min?: string; q?: string; page?: string }>
}) {
  const params = await searchParams
  const decision = params.decision ?? 'all'
  const windowFilter = params.window ?? ''
  const urgencyFilter = params.urgency ?? ''
  const scoreMin = params.score_min ?? ''
  const searchQuery = params.q ?? ''
  const page = Number(params.page ?? 1)

  const activeFilters: Record<string, string> = {}
  if (decision !== 'all') activeFilters.decision = decision
  if (windowFilter) activeFilters.window = windowFilter
  if (urgencyFilter) activeFilters.urgency = urgencyFilter
  if (scoreMin) activeFilters.score_min = scoreMin
  if (searchQuery) activeFilters.q = searchQuery

  const [metrics, list] = await Promise.all([
    getMetrics(),
    getOpportunities(activeFilters, page),
  ])

  const totalPages = list ? Math.ceil(list.total / list.size) : 1

  return (
    <div className="page">
      {/* Topbar */}
      <div className="topbar" style={{ margin: '-20px -24px 0', width: 'calc(100% + 48px)' }}>
        <div className="topbar-title" style={{ flex: 0 }}>
          Oportunidades <span>— pipeline activo</span>
        </div>
        <SearchBar />
        <div style={{ flex: 1 }}></div>
        {metrics && (
          <>
            <span className="chip chip-go">GO: {metrics.total_go}</span>
            <span className="chip chip-warn">Pend: {metrics.total_pending}</span>
            <span className="chip chip-nogo">No-Go: {metrics.total_no_go}</span>
            <span className="chip chip-muted">Total: {metrics.total_detected}</span>
          </>
        )}
      </div>

      {/* Banner de búsqueda activa */}
      {searchQuery && (
        <div style={{ marginTop: 16, padding: '10px 14px', background: 'var(--amber-bg)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: 'var(--r)', fontSize: 12, color: 'var(--amber)', display: 'flex', alignItems: 'center', gap: 8 }}>
          🔍 Resultados para <strong>"{searchQuery}"</strong>
          {list && <span style={{ color: 'var(--muted2)' }}>— {list.total} oportunidades</span>}
        </div>
      )}

      {/* Controles de scraper */}
      <div style={{ marginTop: 20, paddingBottom: 8 }}>
        <ScraperControls source="grantsgov" title="Ejecutar Scraper Global" />
      </div>

      {/* Filtros — decisión */}
      <div className="filters" style={{ marginTop: 20 }}>
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', alignSelf: 'center', marginRight: 4 }}>
          Decisión:
        </span>
        {DECISION_FILTERS.map((f) => (
          <Link
            key={f.key}
            href={buildFilterUrl({ ...activeFilters }, 'decision', f.key)}
            className={`filter-btn ${decision === f.key ? 'on' : ''}`}
          >
            {f.label}
          </Link>
        ))}
      </div>

      {/* Filtros — ventana de mercado */}
      <div className="filters">
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', alignSelf: 'center', marginRight: 4 }}>
          Ventana:
        </span>
        {WINDOW_FILTERS.map((f) => (
          <Link
            key={f.key}
            href={buildFilterUrl(activeFilters, 'window', f.key)}
            className={`filter-btn ${windowFilter === f.key ? 'on' : ''}`}
          >
            {f.label}
          </Link>
        ))}
      </div>

      {/* Filtros — urgencia y otros */}
      <div className="filters">
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', alignSelf: 'center', marginRight: 4 }}>
          Otros:
        </span>
        {URGENCY_FILTERS.map((f) => (
          <Link
            key={f.key}
            href={buildFilterUrl(activeFilters, 'urgency', f.key)}
            className={`filter-btn ${urgencyFilter === f.key ? 'on' : ''}`}
          >
            {f.label}
          </Link>
        ))}
        <Link
          href={buildFilterUrl(activeFilters, 'score_min', '6')}
          className={`filter-btn ${scoreMin === '6' ? 'on' : ''}`}
        >
          Score ≥6
        </Link>
        <Link
          href={buildFilterUrl(activeFilters, 'score_min', '8')}
          className={`filter-btn ${scoreMin === '8' ? 'on' : ''}`}
        >
          Score ≥8
        </Link>
        {Object.keys(activeFilters).length > 0 && (
          <Link href="/" className="filter-btn" style={{ color: 'var(--nogo)', borderColor: 'rgba(248,113,113,0.3)' }}>
            ✕ Limpiar filtros
          </Link>
        )}
      </div>

      {/* Banner criterios scoring */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r)', padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', flexShrink: 0, fontSize: 10.5 }}>
        <span style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)' }}>
          Criterios scoring IA
        </span>
        {[
          ['C1', 'Alineación estratégica'],
          ['C2', 'Ajuste del modelo'],
          ['C3', 'Coherencia ticket'],
          ['C4', 'Viabilidad operativa'],
          ['C5', 'Potencial relacional'],
        ].map(([c, l]) => (
          <div key={c} style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--muted2)' }}>
            <span style={{ background: 'var(--bg4)', color: 'var(--blue)', fontFamily: 'var(--mono)', fontSize: 10, padding: '1px 6px', borderRadius: 3 }}>{c}</span>
            {l}
          </div>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center', borderLeft: '1px solid var(--border)', paddingLeft: 12 }}>
          <span className="crit crit-2">·2 Cumple</span>
          <span className="crit crit-1">·1 Parcial</span>
          <span className="crit crit-0">·0 No cumple</span>
          <span style={{ fontSize: 9.5, color: 'var(--muted)', marginLeft: 4 }}>GO si total ≥6/10</span>
        </div>
      </div>

      {/* Grid de cards */}
      {!list || list.items.length === 0 ? (
        <div className="empty-state">
          <strong>Sin oportunidades en este filtro.</strong><br />
          {decision === 'go'
            ? 'Aún no hay oportunidades GO. Corre el rescore con cuota Gemini fresca para puntuar las 367 detectadas.'
            : 'Cambia los filtros o limpia para ver todas.'}
        </div>
      ) : (
        <>
          <div className="opp-grid">
            {list.items.map((opp) => {
              const dl = daysLabel(opp.deadline)
              const sd = opp.score_details ?? {}
              const crits = [sd.c1, sd.c2, sd.c3, sd.c4, sd.c5]
              const title = decodeHtml(opp.title)
              const description = opp.description ? decodeHtml(opp.description) : null
              const orgName = opp.source_name === 'grantsgov' ? 'Grants.gov / US Federal' : (opp.source_name || 'Sin fuente')
              const sourceBadge = opp.source_name === 'grantsgov' ? '🇺🇸 Scraped' : '◉ Scraped'

              return (
                <div key={opp.id} className={`opp-card ${cardCls(opp.decision)}`}>
                  {/* Header: título + score + meta */}
                  <div className="opp-top">
                    <div style={{ flex: 1 }}>
                      <Link href={`/opportunities/${opp.id}`} className="opp-title" style={{ textDecoration: 'none', display: 'block' }}>
                        {title}
                      </Link>
                      <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                        {dl.chipText !== '—' && (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                            <span style={{ width: 6, height: 6, borderRadius: '50%', background: dl.cls.includes('urgent') ? 'var(--nogo)' : dl.cls.includes('med') ? 'var(--amber)' : 'var(--muted)' }}></span>
                            <span style={{ fontFamily: 'var(--mono)' }}>⏱ {dl.text}</span>
                          </span>
                        )}
                        <span style={{
                          fontSize: 9.5, fontWeight: 600, letterSpacing: '0.5px', textTransform: 'uppercase',
                          color: 'var(--blue)', background: 'var(--blue-bg)', border: '1px solid rgba(96,165,250,0.3)',
                          padding: '1px 7px', borderRadius: 3,
                        }} title="Oportunidad scrapeada de fuente pública">
                          {sourceBadge}
                        </span>
                      </div>
                    </div>
                    <div className={`score-circle ${scoreCircleCls(opp.score_total, opp.decision)}`}>
                      {opp.score_total != null ? `${opp.score_total}/10` : '—'}
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="opp-meta">
                    {opp.market_window && (
                      <span className="tag tag-window">{WINDOW_LABEL[opp.market_window] ?? opp.market_window}</span>
                    )}
                    {opp.capital_type && (
                      <span className="tag tag-capital">{opp.capital_type}</span>
                    )}
                    {opp.source_name && (
                      <span className="tag tag-source">{opp.source_name}</span>
                    )}
                  </div>

                  {/* Descripción */}
                  {description && (
                    <div className="opp-desc">
                      {description.length > 220 ? description.slice(0, 220) + '…' : description}
                    </div>
                  )}

                  {/* Información de contacto: Organización + CEO */}
                  <div className="opp-info-grid">
                    <div className="opp-info-block">
                      <div className="info-role">Organización</div>
                      <div className="info-name">{orgName}</div>
                      {opp.org_email ? (
                        <div className="info-detail" style={{ color: 'var(--blue)' }}>
                          <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: opp.org_email_verified ? 'var(--go)' : 'var(--amber)', marginRight: 5 }}></span>
                          {opp.org_email}
                        </div>
                      ) : (
                        <div className="info-detail" style={{ color: 'var(--muted)', fontStyle: 'italic' }}>
                          ⚠ Sin email · Apollo S5
                        </div>
                      )}
                      {opp.org_website && (
                        <a
                          href={opp.org_website}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ fontSize: 10.5, color: 'var(--muted2)', fontFamily: 'var(--mono)', display: 'block', marginTop: 2 }}
                        >
                          {opp.org_website.replace(/^https?:\/\//, '')}
                        </a>
                      )}
                    </div>
                    <div className="opp-info-block">
                      <div className="info-role">CEO / Representante</div>
                      {opp.ceo_name ? (
                        <>
                          <div className="info-name">{opp.ceo_name}</div>
                          {opp.ceo_title && (
                            <div style={{ fontSize: 10.5, color: 'var(--muted2)', marginBottom: 3 }}>
                              {opp.ceo_title}
                            </div>
                          )}
                          {opp.ceo_email && (
                            <div className="info-detail" style={{ color: 'var(--blue)' }}>
                              <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: opp.ceo_email_verified ? 'var(--go)' : 'var(--amber)', marginRight: 5 }}></span>
                              {opp.ceo_email}
                            </div>
                          )}
                          {opp.ceo_linkedin_url && (
                            <a
                              href={opp.ceo_linkedin_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ fontSize: 10, color: '#0A66C2', fontFamily: 'var(--mono)', display: 'inline-flex', alignItems: 'center', gap: 3, background: 'rgba(10,102,194,0.1)', padding: '1px 6px', borderRadius: 3, marginTop: 4 }}
                            >
                              <span style={{ fontWeight: 700 }}>in</span> LinkedIn
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
                  </div>

                  {/* Acciones */}
                  <div className="opp-links">
                    <Link href={`/opportunities/${opp.id}`} className="link-btn primary">
                      → Ver detalle
                    </Link>
                    {opp.url_rfp && (
                      <a href={opp.url_rfp} target="_blank" rel="noopener noreferrer" className="link-btn">
                        ↗ Ver convocatoria
                      </a>
                    )}
                    {opp.org_website && (
                      <a href={opp.org_website} target="_blank" rel="noopener noreferrer" className="link-btn">
                        ⌘ Sitio organización
                      </a>
                    )}
                    {opp.ceo_email ? (
                      <a
                        href={`mailto:${opp.ceo_email}?subject=${encodeURIComponent('Oportunidad ' + title + ' - aeioTU')}`}
                        className="link-btn"
                        style={!opp.ceo_email_verified ? { color: 'var(--amber)', borderColor: 'rgba(251,191,36,0.3)' } : {}}
                      >
                        {opp.ceo_email_verified ? '✉ Contactar CEO' : '⚠ Contactar CEO (sin verificar)'}
                      </a>
                    ) : (
                      <span className="link-btn" style={{ color: 'var(--muted)', cursor: 'not-allowed', opacity: 0.5 }} title="CEO pendiente Apollo S5">
                        ✉ CEO no disponible
                      </span>
                    )}
                  </div>

                  {/* Bottom: monto + cierre */}
                  <div className="opp-bottom">
                    <div className="opp-amount">{formatAmount(opp)}</div>
                    <div className={`opp-deadline ${dl.cls}`}>⏱ {dl.text}</div>
                  </div>

                  {/* Score bar */}
                  {opp.score_total != null && (
                    <div className="score-bar">
                      <div
                        className={`score-fill ${opp.decision === 'go' ? 'sf-go' : opp.decision === 'pending' ? 'sf-warn' : 'sf-no'}`}
                        style={{ width: `${(opp.score_total / 10) * 100}%` }}
                      />
                    </div>
                  )}

                  {/* Criteria pills */}
                  {opp.score_total != null && (
                    <div className="criteria-row">
                      {crits.map((pts, i) => (
                        <span key={i} className={`crit crit-${pts ?? 0}`}>
                          C{i + 1}·{pts ?? 0}
                        </span>
                      ))}
                      <div className="crit-legend">
                        <span className="cl-item"><span className="cl-dot" style={{ background: 'var(--go)' }}></span>2 pts</span>
                        <span className="cl-item"><span className="cl-dot" style={{ background: 'var(--amber)' }}></span>1 pt</span>
                        <span className="cl-item"><span className="cl-dot" style={{ background: 'var(--bg4)' }}></span>0 pts</span>
                      </div>
                    </div>
                  )}

                  {/* Reasoning del LLM (si existe y es válido) */}
                  {sd.llm_justification
                    && !sd.llm_justification.startsWith('LLM error')
                    && !sd.llm_justification.startsWith('LLM scoring not available')
                    && !sd.llm_justification.includes('no API key')
                    && (
                    <div style={{ background: 'var(--go-bg)', border: '1px solid var(--go-bdr)', borderRadius: 8, padding: '8px 10px', marginTop: 10, fontSize: 11, color: 'var(--go)', lineHeight: 1.5, fontStyle: 'italic' }}>
                      "{sd.llm_justification.length > 200 ? sd.llm_justification.slice(0, 200) + '…' : sd.llm_justification}"
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Paginación */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
            <div style={{ fontSize: 11, color: 'var(--muted)' }}>
              Mostrando {list.items.length} de {list.total} · página {list.page} de {totalPages}
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              {page > 1 && (
                <Link href={`/?${new URLSearchParams({ ...activeFilters, page: String(page - 1) })}`} className="filter-btn">
                  ← Anterior
                </Link>
              )}
              {page < totalPages && (
                <Link href={`/?${new URLSearchParams({ ...activeFilters, page: String(page + 1) })}`} className="filter-btn">
                  Siguiente →
                </Link>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
