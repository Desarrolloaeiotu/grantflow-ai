'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { NATIONAL_OPPS, type NationalOpp } from '../lib/nationalOpps'

interface ScrapedOpp {
  id: string
  title: string
  score_total?: number
  decision?: string
  url_rfp: string
  funder_name: string
}

const CATEGORY_COUNTS: Record<string, number> = NATIONAL_OPPS.reduce((acc, o) => {
  acc[o.category] = (acc[o.category] ?? 0) + 1
  return acc
}, {} as Record<string, number>)

function applyFilter(opps: NationalOpp[], filter: string): NationalOpp[] {
  switch (filter) {
    case 'gobierno':
      return opps.filter((o) => o.category === 'gobierno' || o.category === 'politica')
    case 'privado':
      return opps.filter((o) => o.category === 'privado')
    case 'cajas':
      return opps.filter((o) => o.category === 'cajas')
    case 'alta':
      return opps.filter((o) => o.score >= 8)
    case 'fechas':
      return opps.filter((o) => o.startQuarter <= 2)
    case 'monto':
      return opps.filter((o) => o.amountMinM >= 280)
    default:
      return opps
  }
}

function scoreCircleCls(score: number, decision: string): string {
  if (decision === 'go') return 'sc-go'
  if (score >= 6) return 'sc-go'
  if (score >= 4) return 'sc-warn'
  return 'sc-no'
}

function critCls(pts: number): string {
  if (pts === 2) return 'crit-2'
  if (pts === 1) return 'crit-1'
  return 'crit-0'
}

export default function NacionalPage() {
  const searchParams = useSearchParams()
  const [scrapedOpps, setScrapedOpps] = useState<ScrapedOpp[]>([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  const handleExportCSV = async () => {
    setExporting(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const res = await fetch(`${apiUrl}/api/v1/opportunities/export?decision=`)
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `grantflow_colombia_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export error:', err)
      alert('Error al exportar. Verifica que el backend esté activo.')
    } finally {
      setExporting(false)
    }
  }

  const filter = searchParams.get('filter') ?? 'all'

  useEffect(() => {
    const fetchScrapedOpps = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const url = `${apiUrl}/api/v1/opportunities?source=nacional_colombia&window=funding_colombia&size=100`
        console.log('[Nacional] Fetching from:', url)

        const res = await fetch(url, { cache: 'no-store' })
        console.log('[Nacional] Response status:', res.status)

        if (res.ok) {
          const data = await res.json()
          console.log('[Nacional] Data received:', data)
          setScrapedOpps(data.items || [])
        } else {
          console.error('[Nacional] API error:', res.status, res.statusText)
        }
      } catch (err) {
        console.error('[Nacional] Fetch error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchScrapedOpps()
  }, [])

  const totalGo = NATIONAL_OPPS.filter((o) => o.decision === 'go').length
  const totalPending = NATIONAL_OPPS.filter((o) => o.decision === 'pending').length
  const totalScraped = scrapedOpps.length
  const filtered = applyFilter(NATIONAL_OPPS, filter)

  const FILTERS = [
    { key: 'all',      label: `Curadas (${NATIONAL_OPPS.length})` },
    { key: 'gobierno', label: `Gobierno (${(CATEGORY_COUNTS.gobierno ?? 0) + (CATEGORY_COUNTS.politica ?? 0)})` },
    { key: 'privado',  label: `Privado (${CATEGORY_COUNTS.privado ?? 0})` },
    { key: 'cajas',    label: `Cajas Comp. (${CATEGORY_COUNTS.cajas ?? 0})` },
    { key: 'alta',     label: 'ALTA alineación' },
    { key: 'fechas',   label: 'Próximas fechas (Q1-Q2)' },
    { key: 'monto',    label: '≥$280M' },
  ]

  return (
    <div className="page">
      <div className="topbar" style={{ margin: '-20px -24px 0', width: 'calc(100% + 48px)' }}>
        <div className="topbar-title">
          Nacional Colombia <span>— oportunidades estratégicas 2026 + detectadas</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={async () => {
              try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
                const res = await fetch(`${apiUrl}/api/v1/scrape/run?source=nacional_colombia`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                })
                if (res.ok) {
                  setTimeout(() => window.location.reload(), 1000)
                }
              } catch (err) {
                console.error('Scraper error:', err)
              }
            }}
            style={{
              padding: '5px 12px',
              background: '#059669',
              color: '#fff',
              border: 'none',
              borderRadius: 5,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
            title="Ejecuta el scraper automático para detectar nuevas oportunidades"
          >
            ▶ Scraper
          </button>
        </div>
        <span className="chip chip-go">GO: {totalGo}</span>
        <span className="chip chip-warn">Pendiente: {totalPending}</span>
        <span className="chip chip-muted">Curadas: {NATIONAL_OPPS.length}</span>
        <span className="chip chip-blue">Detectadas: {totalScraped}</span>
        <button
          onClick={handleExportCSV}
          disabled={exporting}
          style={{
            marginLeft: 'auto',
            padding: '6px 14px',
            background: exporting ? '#9ca3af' : '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            fontSize: 13,
            fontWeight: 600,
            cursor: exporting ? 'not-allowed' : 'pointer',
          }}
        >
          {exporting ? 'Exportando…' : '⬇ Descargar CSV'}
        </button>
      </div>

      {/* KPIs */}
      <div className="kpi-row kpi-row-5" style={{ marginTop: 20 }}>
        <div className="kpi go">
          <div className="kpi-label">Oportunidades</div>
          <div className="kpi-val go">{NATIONAL_OPPS.length}</div>
          <div className="kpi-sub">Consultorías potenciales 2026</div>
        </div>
        <div className="kpi blue">
          <div className="kpi-label">Monto potencial</div>
          <div className="kpi-val blue">$1.32B</div>
          <div className="kpi-sub">COP · suma rangos max</div>
        </div>
        <div className="kpi warn">
          <div className="kpi-label">Alineación</div>
          <div className="kpi-val warn">ALTA</div>
          <div className="kpi-sub">Líneas aeioTU activas</div>
        </div>
        <div className="kpi violet">
          <div className="kpi-label">Financiadores</div>
          <div className="kpi-val violet">8</div>
          <div className="kpi-sub">MEN · ICBF · Cajas · Fund.</div>
        </div>
        <div className="kpi red">
          <div className="kpi-label">Niños alcanzados 2025</div>
          <div className="kpi-val red">395K</div>
          <div className="kpi-sub">Indirecto · consultorías</div>
        </div>
      </div>

      <div className="section-hd">
        <h2>
          Oportunidades nacionales 2026 <em>— Colombia es prioridad</em>
        </h2>
      </div>

      {/* Filtros funcionales */}
      <div className="filters">
        {FILTERS.map((f) => (
          <Link
            key={f.key}
            href={f.key === 'all' ? '/nacional' : `/nacional?filter=${f.key}`}
            className={`filter-btn ${filter === f.key ? 'on' : ''}`}
          >
            {f.label}
          </Link>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <strong>Ningún resultado para este filtro.</strong>
        </div>
      ) : (
        <div className="opp-grid">
          {filtered.map((opp) => (
            <div key={opp.id} className={`opp-card ${opp.decision === 'go' ? 'go-card' : 'pend-card'}`}>
              {/* Header con título + score + fecha */}
              <div className="opp-top">
                <div style={{ flex: 1 }}>
                  <Link href={`/nacional/${opp.id}`} className="opp-title" style={{ textDecoration: 'none', display: 'block' }}>
                    {opp.title}
                  </Link>
                  <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--amber)' }}></span>
                      <span style={{ fontFamily: 'var(--mono)' }}>⏱ {opp.deadlineText}</span>
                    </span>
                    <span
                      style={{
                        fontSize: 9.5,
                        fontWeight: 600,
                        letterSpacing: '0.5px',
                        textTransform: 'uppercase',
                        color: 'var(--violet)',
                        background: 'var(--violet-bg)',
                        border: '1px solid rgba(167,139,250,0.3)',
                        padding: '1px 7px',
                        borderRadius: 3,
                      }}
                      title="Oportunidad estratégica curada del plan 2026 — no proviene de una convocatoria pública específica"
                    >
                      ◆ Estratégica · Curada
                    </span>
                  </div>
                </div>
                <div className={`score-circle ${scoreCircleCls(opp.score, opp.decision)}`}>
                  {opp.score}/10
                </div>
              </div>

              <div className="opp-meta">
                {opp.tags.map((t, i) => (
                  <span key={i} className={`tag ${t.cls}`}>
                    {t.label}
                  </span>
                ))}
              </div>

              <div className="opp-desc">{opp.description}</div>

              {/* Acciones aeioTU */}
              <div style={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px', marginBottom: 10 }}>
                <div style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
                  Acciones aeioTU
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {opp.actions.map((a) => (
                    <div key={a.step} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 11, color: 'var(--muted2)', lineHeight: 1.5 }}>
                      <span style={{ width: 16, height: 16, borderRadius: '50%', background: 'var(--bg4)', color: 'var(--accent)', fontSize: 9, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1, fontFamily: 'var(--mono)' }}>
                        {a.step}
                      </span>
                      <span>{a.text}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Contactos: Organización + CEO */}
              <div className="opp-info-grid">
                <div className="opp-info-block">
                  <div className="info-role">Organización</div>
                  <div className="info-name">{opp.organization.name}</div>
                  <div className="info-detail" style={{ color: 'var(--blue)' }}>
                    <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: opp.organization.verified ? 'var(--go)' : 'var(--amber)', marginRight: 5 }} title={opp.organization.verified ? 'Verificado Apollo' : 'Pendiente verificación Apollo'}></span>
                    {opp.organization.email}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
                    <a
                      href={opp.organization.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ fontSize: 10.5, color: 'var(--muted2)', fontFamily: 'var(--mono)' }}
                    >
                      {opp.organization.website.replace(/^https?:\/\//, '')}
                    </a>
                    {opp.organization.linkedin && (
                      <a
                        href={opp.organization.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: 10, color: '#0A66C2', fontFamily: 'var(--mono)', display: 'inline-flex', alignItems: 'center', gap: 3, background: 'rgba(10,102,194,0.1)', padding: '1px 6px', borderRadius: 3 }}
                        title="LinkedIn de la organización"
                      >
                        <span style={{ fontWeight: 700 }}>in</span> LinkedIn
                      </a>
                    )}
                  </div>
                </div>
                <div className="opp-info-block">
                  <div className="info-role">CEO / Representante</div>
                  <div className="info-name">{opp.ceo.name}</div>
                  <div style={{ fontSize: 10.5, color: 'var(--muted2)', marginBottom: 3 }}>
                    {opp.ceo.title}
                  </div>
                  <div className="info-detail" style={{ color: 'var(--blue)' }}>
                    <span
                      style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: opp.ceo.verified ? 'var(--go)' : 'var(--amber)', marginRight: 5 }}
                      title={opp.ceo.verified ? 'Verificado Apollo' : 'Pendiente Apollo.io (Sprint S5)'}
                    ></span>
                    {opp.ceo.email}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                    {opp.ceo.linkedin && (
                      <a
                        href={opp.ceo.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ fontSize: 10, color: '#0A66C2', fontFamily: 'var(--mono)', display: 'inline-flex', alignItems: 'center', gap: 3, background: 'rgba(10,102,194,0.1)', padding: '1px 6px', borderRadius: 3 }}
                        title="Buscar en LinkedIn"
                      >
                        <span style={{ fontWeight: 700 }}>in</span> Buscar persona
                      </a>
                    )}
                    {!opp.ceo.verified && (
                      <span style={{ fontSize: 9.5, color: 'var(--amber)', fontStyle: 'italic' }}>
                        ⚠ Pendiente Apollo
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Aliado (si existe) */}
              {opp.ally && (
                <div style={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px', marginBottom: 10, fontSize: 11 }}>
                  <span style={{ color: 'var(--muted)', fontSize: 9.5, fontWeight: 600, letterSpacing: '0.8px', textTransform: 'uppercase', marginRight: 8 }}>
                    {opp.ally.role ?? 'Aliado'}:
                  </span>
                  <span style={{ color: 'var(--text)', fontWeight: 500 }}>{opp.ally.name}</span>
                  {opp.ally.email && (
                    <span style={{ marginLeft: 10, color: 'var(--blue)', fontFamily: 'var(--mono)', fontSize: 10.5 }}>
                      <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: opp.ally.verified ? 'var(--go)' : 'var(--amber)', marginRight: 5 }}></span>
                      {opp.ally.email}
                    </span>
                  )}
                </div>
              )}

              {/* Botones de acción */}
              <div className="opp-links">
                <Link href={`/nacional/${opp.id}`} className="link-btn primary">
                  → Ver detalle completo
                </Link>
                <a
                  href={opp.rfpUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                  title="Sitio oficial de la organización financiadora"
                >
                  ↗ Programa institucional
                </a>
                <a
                  href={opp.organization.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                >
                  ⌘ Sitio organización
                </a>
                {opp.organization.linkedin && (
                  <a
                    href={opp.organization.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="link-btn"
                    style={{ color: '#0A66C2', borderColor: 'rgba(10,102,194,0.3)' }}
                    title="Página de LinkedIn de la organización"
                  >
                    <span style={{ fontWeight: 700 }}>in</span> LinkedIn
                  </a>
                )}
                <a
                  href={`mailto:${opp.ceo.email}?subject=${encodeURIComponent('Oportunidad ' + opp.title + ' - aeioTU')}`}
                  className="link-btn"
                  style={!opp.ceo.verified ? { color: 'var(--amber)', borderColor: 'rgba(251,191,36,0.3)' } : {}}
                  title={opp.ceo.verified ? 'Email verificado por Apollo' : 'Email pendiente de verificación Apollo'}
                >
                  {opp.ceo.verified ? '✉ Contactar CEO' : '⚠ Contactar CEO (sin verificar)'}
                </a>
              </div>

              {/* Bottom */}
              <div className="opp-bottom">
                <div className="opp-amount">{opp.amountCOP}</div>
                <div className="opp-deadline">⏱ {opp.deadlineText}</div>
              </div>

              <div className="score-bar">
                <div
                  className={`score-fill ${opp.decision === 'go' ? 'sf-go' : 'sf-warn'}`}
                  style={{ width: `${(opp.score / 10) * 100}%` }}
                />
              </div>

              <div className="criteria-row">
                {opp.criteria.map((c, i) => (
                  <span key={i} className={`crit ${critCls(c.pts)}`} title={c.label}>
                    C{i + 1}·{c.pts} {c.label}
                  </span>
                ))}
              </div>

              <div style={{ background: 'var(--go-bg)', border: '1px solid var(--go-bdr)', borderRadius: 8, padding: '8px 10px', marginTop: 10, fontSize: 11, color: 'var(--go)', lineHeight: 1.5, fontStyle: 'italic' }}>
                "{opp.reasoning}"
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Sección: Oportunidades detectadas por scraping */}
      <div style={{ marginTop: 48 }}>
        <div className="section-hd">
          <h2>
            Oportunidades detectadas por scraping <em>— ICBF, Google News + otras fuentes</em>
          </h2>
        </div>

        {loading ? (
          <div className="empty-state">
            <strong>Cargando oportunidades detectadas...</strong>
          </div>
        ) : scrapedOpps.length === 0 ? (
          <div className="empty-state">
            <strong>No hay oportunidades detectadas aún.</strong>
            <p>Ejecuta el scraper para poblar esta sección.</p>
          </div>
        ) : (
          <div className="opp-grid">
            {scrapedOpps.map((opp) => (
              <div key={opp.id} className={`opp-card ${opp.decision === 'go' ? 'go-card' : 'pend-card'}`}>
                <div className="opp-top">
                  <div style={{ flex: 1 }}>
                    <a href={opp.url_rfp} target="_blank" rel="noopener noreferrer" className="opp-title" style={{ textDecoration: 'none', display: 'block' }}>
                      {opp.title}
                    </a>
                    <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 4 }}>
                      <span style={{ background: 'var(--blue-bg)', color: 'var(--blue)', padding: '2px 8px', borderRadius: 3, fontSize: 9.5, fontWeight: 600 }}>
                        ◆ Scraping automático
                      </span>
                    </div>
                  </div>
                  {opp.score_total && (
                    <div className={`score-circle ${scoreCircleCls(opp.score_total, opp.decision || 'pending')}`}>
                      {opp.score_total}/10
                    </div>
                  )}
                </div>

                <div style={{ fontSize: 11, color: 'var(--muted2)', margin: '10px 0' }}>
                  <strong>Financiador:</strong> {opp.funder_name}
                </div>

                <div className="opp-links">
                  <a
                    href={opp.url_rfp}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="link-btn primary"
                  >
                    → Ver convocatoria
                  </a>
                </div>

                <div style={{ background: 'var(--blue-bg)', border: '1px solid var(--blue-bdr)', borderRadius: 8, padding: '8px 10px', marginTop: 10, fontSize: '10.5px', color: 'var(--blue)', lineHeight: 1.5 }}>
                  Oportunidad detectada automáticamente por el scraper nacional_colombia. Requiere validación manual.
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
