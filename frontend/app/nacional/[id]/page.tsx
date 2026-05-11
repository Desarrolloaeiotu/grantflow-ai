import { Fragment } from 'react'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { NATIONAL_OPPS } from '../../lib/nationalOpps'

const CATEGORY_LABEL: Record<string, string> = {
  gobierno: 'Gobierno',
  privado: 'Sector privado',
  cajas: 'Cajas de Compensación',
  politica: 'Política Pública',
}

function critCls(pts: number): string {
  if (pts === 2) return 'crit-2'
  if (pts === 1) return 'crit-1'
  return 'crit-0'
}

function scoreCircleCls(score: number, decision: string): string {
  if (decision === 'go') return 'sc-go'
  if (score >= 6) return 'sc-go'
  if (score >= 4) return 'sc-warn'
  return 'sc-no'
}

export default async function NacionalDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const opp = NATIONAL_OPPS.find((o) => o.id === id)
  if (!opp) notFound()

  // Otras oportunidades nacionales de la misma categoría
  const related = NATIONAL_OPPS.filter((o) => o.id !== id && o.category === opp.category).slice(0, 3)
  // Si no hay de la misma categoría, mostrar 2 cualquiera diferentes
  const fallback = related.length === 0 ? NATIONAL_OPPS.filter((o) => o.id !== id).slice(0, 2) : related

  return (
    <div className="page">
      {/* Topbar */}
      <div className="topbar" style={{ margin: '-20px -24px 0', width: 'calc(100% + 48px)' }}>
        <div className="topbar-title" style={{ fontSize: 16 }}>
          <Link href="/nacional" style={{ color: 'var(--muted)', marginRight: 8 }}>← Nacional Colombia</Link>
          <span>· detalle</span>
        </div>
        <span className={`chip chip-${opp.decision === 'go' ? 'go' : 'warn'}`}>
          {opp.decision === 'go' ? 'GO' : 'PENDIENTE'}
        </span>
        <span className="chip chip-go">Score {opp.score}/10</span>
        <span
          className="chip"
          style={{
            color: 'var(--violet)',
            background: 'var(--violet-bg)',
            border: '1px solid rgba(167,139,250,0.3)',
          }}
        >
          ◆ {CATEGORY_LABEL[opp.category]}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, marginTop: 20, alignItems: 'start' }}>

        {/* ── Columna principal ─────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Header */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 22, borderLeft: `3px solid ${opp.decision === 'go' ? 'var(--go)' : 'var(--amber)'}` }}>
            <h1 style={{ fontFamily: 'var(--serif)', fontSize: 24, lineHeight: 1.3, color: 'var(--text)', marginBottom: 14, fontWeight: 400 }}>
              {opp.title}
            </h1>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
              {opp.tags.map((t, i) => (
                <span key={i} className={`tag ${t.cls}`}>
                  {t.label}
                </span>
              ))}
            </div>

            <div style={{ fontSize: 13, color: 'var(--muted2)', lineHeight: 1.7, padding: '12px 16px', borderLeft: '2px solid var(--border2)', background: 'var(--bg3)', borderRadius: 6 }}>
              {opp.description}
            </div>
          </div>

          {/* Acciones aeioTU (pasos) */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 14 }}>
              Acciones aeioTU — pasos del plan
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {opp.actions.map((a) => (
                <div key={a.step} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: '10px 14px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8 }}>
                  <span style={{ width: 26, height: 26, borderRadius: '50%', background: 'var(--bg4)', color: 'var(--accent)', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontFamily: 'var(--mono)' }}>
                    {a.step}
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.6, flex: 1 }}>
                    {a.text}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Acciones / enlaces externos */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 10 }}>
              Enlaces y contacto
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <a href={opp.rfpUrl} target="_blank" rel="noopener noreferrer" className="link-btn primary">
                → Programa institucional
              </a>
              <a href={opp.organization.website} target="_blank" rel="noopener noreferrer" className="link-btn">
                ⌘ Sitio organización
              </a>
              {opp.organization.linkedin && (
                <a
                  href={opp.organization.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                  style={{ color: '#0A66C2', borderColor: 'rgba(10,102,194,0.3)' }}
                >
                  <span style={{ fontWeight: 700 }}>in</span> LinkedIn org
                </a>
              )}
              <a
                href={`mailto:${opp.ceo.email}?subject=${encodeURIComponent('Oportunidad ' + opp.title + ' - aeioTU')}`}
                className="link-btn"
                style={!opp.ceo.verified ? { color: 'var(--amber)', borderColor: 'rgba(251,191,36,0.3)' } : {}}
              >
                {opp.ceo.verified ? '✉ Contactar CEO' : '⚠ Contactar CEO (sin verificar)'}
              </a>
              {opp.ceo.linkedin && (
                <a
                  href={opp.ceo.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                  style={{ color: '#0A66C2', borderColor: 'rgba(10,102,194,0.3)' }}
                >
                  <span style={{ fontWeight: 700 }}>in</span> Buscar CEO
                </a>
              )}
            </div>
          </div>

          {/* Scoring detallado */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 14 }}>
              Scoring por criterio
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '8px 16px', alignItems: 'center', marginBottom: 14 }}>
              {opp.criteria.map((c, i) => {
                const color = c.pts === 2 ? 'var(--go)' : c.pts === 1 ? 'var(--amber)' : 'var(--muted)'
                return (
                  <Fragment key={i}>
                    <span style={{ fontSize: 12, color: 'var(--muted2)' }}>
                      C{i + 1} · {c.label}
                    </span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 500, color, textAlign: 'right' }}>
                      {c.pts}/2
                    </span>
                  </Fragment>
                )
              })}
            </div>

            <div style={{ height: 4, background: 'var(--bg4)', borderRadius: 2, overflow: 'hidden', marginBottom: 14 }}>
              <div style={{
                height: '100%',
                width: `${(opp.score / 10) * 100}%`,
                background: opp.decision === 'go' ? 'linear-gradient(90deg, var(--go), #06D6A0)' : 'linear-gradient(90deg, var(--amber), #F59E0B)',
              }} />
            </div>

            {/* Pills compactas */}
            <div className="criteria-row" style={{ marginBottom: 14 }}>
              {opp.criteria.map((c, i) => (
                <span key={i} className={`crit ${critCls(c.pts)}`}>
                  C{i + 1}·{c.pts} {c.label}
                </span>
              ))}
            </div>

            {/* Reasoning */}
            <div style={{ background: 'var(--go-bg)', border: '1px solid var(--go-bdr)', borderRadius: 8, padding: '10px 12px', fontSize: 12, color: 'var(--go)', lineHeight: 1.6, fontStyle: 'italic' }}>
              "{opp.reasoning}"
              <div style={{ fontStyle: 'normal', color: 'var(--muted)', fontSize: 10, marginTop: 6 }}>
                Razonamiento estratégico aeioTU (curado, no LLM)
              </div>
            </div>
          </div>

          {/* Oportunidades relacionadas */}
          {fallback.length > 0 && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>
                {related.length > 0 ? `Otras en ${CATEGORY_LABEL[opp.category]}` : 'Otras oportunidades nacionales'}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {fallback.map((r) => (
                  <Link
                    key={r.id}
                    href={`/nacional/${r.id}`}
                    style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center', padding: '10px 12px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, textDecoration: 'none' }}
                  >
                    <span style={{ color: 'var(--text)', fontSize: 12.5, fontWeight: 500, flex: 1, lineHeight: 1.4 }}>
                      {r.title}
                    </span>
                    <span style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
                      <span className={`badge ${r.decision === 'go' ? 'badge-go' : 'badge-warn'}`}>
                        {r.decision === 'go' ? 'GO' : 'PEND'}
                      </span>
                      <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--go)', fontWeight: 500 }}>
                        {r.score}/10
                      </span>
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* ── Right rail (sticky) ────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, position: 'sticky', top: 20 }}>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              Monto estimado
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 18, color: 'var(--go)', fontWeight: 500 }}>
              {opp.amountCOP}
            </div>
            <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 4 }}>
              Rango por oportunidad / financiador
            </div>
          </div>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              Ventana de inicio
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 14, color: 'var(--amber)', fontWeight: 500 }}>
              ⏱ {opp.deadlineText}
            </div>
            <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 4 }}>
              Q{opp.startQuarter} 2026 · negociación directa
            </div>
          </div>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              Organización
            </div>
            <div style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500, marginBottom: 4 }}>
              {opp.organization.name}
            </div>
            <a href={opp.organization.website} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--blue)', fontSize: 11, fontFamily: 'var(--mono)', display: 'block', marginBottom: 6 }}>
              {opp.organization.website.replace(/^https?:\/\//, '')} →
            </a>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--blue)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: opp.organization.verified ? 'var(--go)' : 'var(--amber)' }}></span>
              {opp.organization.email}
            </div>
          </div>

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              CEO / Representante
            </div>
            <div style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500 }}>{opp.ceo.name}</div>
            <div style={{ fontSize: 11, color: 'var(--muted2)', marginBottom: 6 }}>{opp.ceo.title}</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--blue)', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: opp.ceo.verified ? 'var(--go)' : 'var(--amber)' }}></span>
              {opp.ceo.email}
            </div>
            {!opp.ceo.verified && (
              <div style={{ fontSize: 9.5, color: 'var(--amber)', fontStyle: 'italic' }}>
                ⚠ Pendiente verificación Apollo.io (S5)
              </div>
            )}
          </div>

          {opp.ally && (
            <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
                {opp.ally.role ?? 'Aliado'}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500, marginBottom: 4 }}>
                {opp.ally.name}
              </div>
              {opp.ally.email && (
                <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--blue)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: opp.ally.verified ? 'var(--go)' : 'var(--amber)' }}></span>
                  {opp.ally.email}
                </div>
              )}
              {opp.ally.website && (
                <a
                  href={opp.ally.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: 'var(--muted2)', fontSize: 10.5, fontFamily: 'var(--mono)', display: 'block', marginTop: 4 }}
                >
                  {opp.ally.website.replace(/^https?:\/\//, '')}
                </a>
              )}
            </div>
          )}

          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
              Metadata
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5, fontSize: 11 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Categoría</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)' }}>{opp.category}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Decisión</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)' }}>{opp.decision}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Score</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)' }}>{opp.score}/10</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Origen</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)', fontSize: 10 }}>Curada CLAUDE.md</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--muted)' }}>Trimestre</span>
                <span style={{ color: 'var(--muted2)', fontFamily: 'var(--mono)' }}>Q{opp.startQuarter} 2026</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
