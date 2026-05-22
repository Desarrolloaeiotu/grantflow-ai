import Link from 'next/link'

interface SourceStats {
  source_name: string
  total: number
  go_count: number
  pending_count: number
  no_go_count: number
  last_detected: string | null
  avg_score: number | null
}

interface Metrics {
  total_detected: number
  total_go: number
  total_pending: number
  total_no_go: number
}

async function getSourceStats(): Promise<SourceStats[]> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboard/sources`, { cache: 'no-store' })
    if (!res.ok) return []
    return res.json()
  } catch { return [] }
}

async function getMetrics(): Promise<Metrics | null> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/dashboard/metrics`, { cache: 'no-store' })
    if (!res.ok) return null
    return res.json()
  } catch { return null }
}

// Catálogo de fuentes configuradas (desde el código del backend)
const SOURCE_CATALOG: Record<string, { display: string; method: string; cost: string; status: 'live' | 'scheduled' | 'inactive' }> = {
  grantsgov:        { display: 'Grants.gov',         method: 'REST API',          cost: 'Gratis',   status: 'live' },
  rss:              { display: 'RSS Feeds (19)',     method: 'RSS Parser',        cost: 'Gratis',   status: 'live' },
  bid:              { display: 'BID Lab / IADB',     method: 'HTML Scraping',     cost: 'Gratis',   status: 'inactive' },
  unwomen:          { display: 'UN Women',           method: 'HTML Scraping',     cost: 'Gratis',   status: 'inactive' },
  developmentaid:   { display: 'DevelopmentAid',     method: 'HTML Scraping',     cost: 'Gratis',   status: 'inactive' },
  apollo:           { display: 'Apollo.io',          method: 'REST API',          cost: '$49/mes',  status: 'scheduled' },
  instrumentl:      { display: 'Instrumentl',        method: 'REST API premium',  cost: '$299/mes', status: 'scheduled' },
}

function timeAgo(iso: string | null): string {
  if (!iso) return 'nunca'
  const ms = Date.now() - new Date(iso).getTime()
  const hours = Math.floor(ms / 3_600_000)
  const days = Math.floor(hours / 24)
  if (days > 1) return `hace ${days}d`
  if (hours > 1) return `hace ${hours}h`
  const mins = Math.floor(ms / 60_000)
  if (mins > 0) return `hace ${mins} min`
  return 'recién'
}

function sourceDisplayName(name: string): string {
  // Maneja "rss:lego_foundation" → "RSS · LEGO Foundation"
  if (name.startsWith('rss:')) {
    const slug = name.slice(4).replace(/_/g, ' ')
    return `RSS · ${slug.replace(/\b\w/g, l => l.toUpperCase())}`
  }
  return SOURCE_CATALOG[name]?.display ?? name
}

export default async function RadarPage() {
  const [sources, metrics] = await Promise.all([
    getSourceStats(),
    getMetrics(),
  ])

  // Stats agregadas
  const activeSourcesCount = sources.length
  const totalOpps = sources.reduce((acc, s) => acc + s.total, 0)
  const totalGo = sources.reduce((acc, s) => acc + s.go_count, 0)

  // Última ingesta global
  const lastIngestIso = sources
    .map(s => s.last_detected)
    .filter((x): x is string => x !== null)
    .sort()
    .reverse()[0] ?? null

  // Fuentes catálogo que NO están en stats (no han traído opps)
  const inactiveSources = Object.entries(SOURCE_CATALOG).filter(
    ([key]) => !sources.some(s => s.source_name === key || s.source_name.startsWith(`${key}:`))
  )

  return (
    <div className="page">
      <div className="topbar" style={{ margin: '-20px -24px 0', width: 'calc(100% + 48px)' }}>
        <div className="topbar-title">
          Radar <span>— estado de ingesta</span>
        </div>
        <span className="chip chip-go" style={{ animation: 'blink 2s infinite' }}>
          ● {activeSourcesCount} fuente{activeSourcesCount === 1 ? '' : 's'} activa{activeSourcesCount === 1 ? '' : 's'}
        </span>
        <span className="chip chip-muted">{totalOpps} total ingestadas</span>
      </div>

      {/* KPIs */}
      <div className="kpi-row" style={{ marginTop: 20 }}>
        <div className="kpi go">
          <div className="kpi-label">Fuentes con data</div>
          <div className="kpi-val go">{activeSourcesCount}</div>
          <div className="kpi-sub">de {Object.keys(SOURCE_CATALOG).length} configuradas</div>
        </div>
        <div className="kpi blue">
          <div className="kpi-label">Opps ingestadas</div>
          <div className="kpi-val blue">{totalOpps}</div>
          <div className="kpi-sub">{totalGo} GO · {metrics?.total_pending ?? 0} pendientes</div>
        </div>
        <div className="kpi warn">
          <div className="kpi-label">Última ingesta</div>
          <div className="kpi-val warn" style={{ fontSize: 16 }}>{timeAgo(lastIngestIso)}</div>
          <div className="kpi-sub">{lastIngestIso ? new Date(lastIngestIso).toLocaleString('es-CO') : '—'}</div>
        </div>
        <div className="kpi violet">
          <div className="kpi-label">Próxima ingesta</div>
          <div className="kpi-val violet" style={{ fontSize: 16 }}>Sprint S4</div>
          <div className="kpi-sub">n8n cron · diario 6am</div>
        </div>
      </div>

      {/* ── Fuentes con datos (activas) ────────────────────────────────────── */}
      <div className="section-hd">
        <h2>
          Fuentes activas <em>— han ingestado al menos 1 oportunidad</em>
        </h2>
      </div>

      {sources.length === 0 ? (
        <div className="empty-state">
          <strong>Sin fuentes activas todavía.</strong><br />
          Ejecuta los scrapers para empezar la ingesta de oportunidades.
        </div>
      ) : (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fuente</th>
                <th style={{ textAlign: 'center' }}>Total</th>
                <th style={{ textAlign: 'center' }}>GO</th>
                <th style={{ textAlign: 'center' }}>Pendiente</th>
                <th style={{ textAlign: 'center' }}>No-Go</th>
                <th style={{ textAlign: 'center' }}>Score prom.</th>
                <th>Última ingesta</th>
                <th style={{ width: 100 }}>Ver opps</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.source_name}>
                  <td>
                    <div style={{ fontWeight: 500, fontSize: 12.5, color: 'var(--text)' }}>
                      {sourceDisplayName(s.source_name)}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--muted)', fontFamily: 'var(--mono)' }}>
                      {s.source_name}
                    </div>
                  </td>
                  <td className="td-mono" style={{ textAlign: 'center', fontWeight: 500 }}>{s.total}</td>
                  <td style={{ textAlign: 'center' }}>
                    {s.go_count > 0
                      ? <span className="badge badge-go">{s.go_count}</span>
                      : <span style={{ color: 'var(--muted)' }}>—</span>}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {s.pending_count > 0
                      ? <span className="badge badge-warn">{s.pending_count}</span>
                      : <span style={{ color: 'var(--muted)' }}>—</span>}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {s.no_go_count > 0
                      ? <span className="badge badge-nogo">{s.no_go_count}</span>
                      : <span style={{ color: 'var(--muted)' }}>—</span>}
                  </td>
                  <td className="td-mono" style={{ textAlign: 'center', color: s.avg_score && s.avg_score >= 6 ? 'var(--go)' : 'var(--muted2)' }}>
                    {s.avg_score != null ? s.avg_score.toFixed(1) : '—'}
                  </td>
                  <td className="td-muted td-mono" style={{ fontSize: 11 }}>
                    {timeAgo(s.last_detected)}
                  </td>
                  <td>
                    <Link
                      href={`/?source=${encodeURIComponent(s.source_name)}`}
                      className="link-btn"
                      style={{ fontSize: 10.5, padding: '3px 8px' }}
                    >
                      → Ver {s.total}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Fuentes configuradas sin data ──────────────────────────────────── */}
      {inactiveSources.length > 0 && (
        <>
          <div className="section-hd">
            <h2>
              Fuentes configuradas sin ingesta <em>— scrapers caídos, pendientes o pagos</em>
            </h2>
          </div>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Fuente</th>
                  <th>Método</th>
                  <th>Costo</th>
                  <th>Estado</th>
                  <th>Notas</th>
                </tr>
              </thead>
              <tbody>
                {inactiveSources.map(([key, info]) => {
                  const statusColors: Record<string, { cls: string; text: string }> = {
                    live:      { cls: 'badge-go',    text: '● Activo' },
                    scheduled: { cls: 'badge-warn',  text: '◌ Sprint S5/S6' },
                    inactive:  { cls: 'badge-nogo',  text: '⚠ Scraper caído' },
                  }
                  const status = statusColors[info.status]
                  const note = info.status === 'inactive'
                    ? 'HTML del sitio cambió. Pendiente ajustar selectores.'
                    : info.status === 'scheduled'
                    ? `Activar en sprint correspondiente.`
                    : '—'
                  return (
                    <tr key={key}>
                      <td style={{ fontWeight: 500 }}>{info.display}</td>
                      <td className="td-muted">{info.method}</td>
                      <td>
                        <span className={info.cost === 'Gratis' ? 'badge badge-go' : 'badge badge-warn'}>
                          {info.cost}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${status.cls}`}>{status.text}</span>
                      </td>
                      <td className="td-muted" style={{ fontSize: 11 }}>{note}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Aclaración del scope */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r)', padding: '12px 16px', fontSize: 11.5, color: 'var(--muted2)', lineHeight: 1.7 }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 6 }}>
          Alcance del Radar
        </div>
        El radar ingestar a la sección <Link href="/" style={{ color: 'var(--blue)' }}>Oportunidades</Link> y alimenta <Link href="/alertas" style={{ color: 'var(--blue)' }}>Alertas</Link> + <Link href="/pipeline" style={{ color: 'var(--blue)' }}>Pipeline</Link>.{' '}
        <Link href="/nacional" style={{ color: 'var(--blue)' }}>Nacional Colombia</Link> es contenido <strong style={{ color: 'var(--violet)' }}>curado estratégico</strong> definido en el CLAUDE.md — no pasa por scrapers ni LLM scoring.
      </div>
    </div>
  )
}
