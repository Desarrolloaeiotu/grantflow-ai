'use client'

import { useState, useEffect } from "react"
import Link from "next/link"
import { Tender, ApiListResponse, formatCOP, formatDate, daysUntilDeadline, getUrgencyLabel, getUrgencyColor } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

function ScoreBadge({ score }: { score: number | null }) {
  if (!score) return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      width: '50px',
      height: '50px',
      borderRadius: '4px',
      background: 'var(--bg2)',
      fontSize: '10px',
      color: 'var(--muted)',
      fontWeight: 600,
      textAlign: 'center',
      lineHeight: 1.2
    }}>
      Sin<br/>score
    </div>
  )

  const max = 10
  const percent = (score / max) * 100
  const color = score >= 6 ? 'var(--go)' : score >= 4 ? '#ff9800' : 'var(--nogo)'

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      width: '50px',
      height: '50px',
      borderRadius: '4px',
      background: 'var(--bg2)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{
        position: 'absolute',
        inset: 0,
        background: color,
        opacity: 0.1
      }} />
      <div style={{
        fontSize: '16px',
        fontWeight: 700,
        color,
        fontFamily: 'monospace',
        zIndex: 1
      }}>
        {score}/{max}
      </div>
    </div>
  )
}

export default function ConvocatoriasGlobalPage() {
  const [tenders, setTenders] = useState<Tender[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [decision, setDecision] = useState<string>("")
  const [window, setWindow] = useState<string>("funding_global")

  useEffect(() => {
    fetchTenders()
  }, [page, decision, window])

  async function fetchTenders() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: "25",
        window: window,
      })

      if (decision) params.append("decision", decision)

      // Changed from /tenders to /opportunities
      const res = await fetch(`${API_URL}/api/v1/opportunities?${params}`)
      if (!res.ok) throw new Error(`API error: ${res.status}`)

      const data: ApiListResponse<Tender> = await res.json()

      setTenders(data.items || [])
      setTotal(data.total || 0)
    } catch (error) {
      console.error("Error fetching opportunities:", error)
      setTenders([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const res = await fetch(`${API_URL}/api/v1/opportunities/export?window=funding_global`)
      const data = await res.json()
      const csv = atob(data.content_base64)
      const blob = new Blob([csv], { type: "text/csv" })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = data.filename
      a.click()
    } catch (error) {
      console.error("Error exporting:", error)
    }
  }

  return (
    <div className="page">
      <div className="section-hd" style={{ marginBottom: '20px' }}>
        <h2>Convocatorias Globales</h2>
        <span className="badge-blue" style={{ marginLeft: 'auto' }}>≥ COP $100M</span>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <select
          value={decision}
          onChange={(e) => {
            setDecision(e.target.value)
            setPage(1)
          }}
          style={{
            padding: '6px 12px',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r)',
            fontSize: '13px',
            background: 'var(--bg2)',
            color: 'var(--text)',
            cursor: 'pointer'
          }}
        >
          <option value="">Todas las decisiones</option>
          <option value="go">GO</option>
          <option value="no_go">NO GO</option>
          <option value="pending">PENDING</option>
        </select>

        <button
          onClick={handleExport}
          className="link-btn primary"
          style={{ marginLeft: 'auto' }}
        >
          📥 Exportar CSV
        </button>
      </div>

      {loading ? (
        <div className="empty-state">Cargando convocatorias...</div>
      ) : tenders.length === 0 ? (
        <div className="empty-state">No hay convocatorias que cumplan los criterios</div>
      ) : (
        <>
          <style>{`
            .tender-card {
              transition: all 0.2s;
            }
            .tender-card:hover {
              background: var(--bg2);
              border-color: var(--border2);
            }
          `}</style>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
            {tenders.map((tender, idx) => {
              const daysLeft = daysUntilDeadline(tender.deadline)

              return (
                <Link href={`/convocatorias/${tender.id}`} key={tender.id} style={{ textDecoration: 'none' }}>
                  <div className="tender-card" style={{
                    background: 'var(--bg)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--r)',
                    padding: '16px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                  }}>
                    {/* Score Badge - Top */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                      <div style={{ flex: 1 }}>
                        <h3 style={{ fontSize: '14px', fontWeight: 700, margin: '0 0 4px 0', color: 'var(--text)' }}>
                          {tender.title}
                        </h3>
                        <p style={{ fontSize: '11px', color: 'var(--muted)', margin: 0 }}>
                          {tender.funder_name}
                        </p>
                      </div>
                      <ScoreBadge score={tender.score_total} />
                    </div>

                    {/* Metadata Grid */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '8px',
                      fontSize: '11px',
                      borderTop: '1px solid var(--border)',
                      borderBottom: '1px solid var(--border)',
                      paddingTop: '8px',
                      paddingBottom: '8px'
                    }}>
                      <div>
                        <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '2px' }}>Monto Máx</div>
                        <div style={{ color: 'var(--text)', fontWeight: 700 }}>
                          {tender.amount_max_cop ? formatCOP(tender.amount_max_cop) : "—"}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '2px' }}>Cierre</div>
                        <div style={{ color: 'var(--text)', fontWeight: 700 }}>
                          {formatDate(tender.deadline) || "—"}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '2px' }}>Días</div>
                        <div style={{ color: daysLeft && daysLeft <= 7 ? 'var(--nogo)' : 'var(--text)', fontWeight: 700 }}>
                          {daysLeft !== null ? daysLeft + 'd' : "—"}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '2px' }}>Fuente</div>
                        <div style={{ color: 'var(--text)', fontWeight: 700 }}>
                          {tender.source_name === 'secop' ? '🏛️ SECOP' : '📰 Noticia'}
                        </div>
                      </div>
                    </div>

                    {/* Badges */}
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {tender.source_name === 'secop' && <span className="badge-go" style={{ fontSize: '10px', padding: '4px 6px', background: '#e3f2fd', color: '#1976d2', border: '1px solid #1976d2' }}>SECOP</span>}
                      {tender.decision === 'go' && <span className="badge-go" style={{ fontSize: '10px', padding: '4px 6px' }}>✓ GO</span>}
                      {tender.decision === 'no_go' && <span className="badge-nogo" style={{ fontSize: '10px', padding: '4px 6px' }}>✗ NO GO</span>}
                      {tender.decision === 'pending' && <span className="badge-warn" style={{ fontSize: '10px', padding: '4px 6px' }}>⏳ PENDING</span>}
                      {daysLeft && daysLeft <= 7 && <span className="badge-nogo" style={{ fontSize: '10px', padding: '4px 6px' }}>URGENTE</span>}
                    </div>
                  </div>
                </Link>
              )
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', fontSize: '12px', color: 'var(--muted)' }}>
            <span>
              Mostrando <strong>{tenders.length}</strong> de <strong>{total}</strong> convocatorias
            </span>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="link-btn"
                style={{ opacity: page === 1 ? 0.5 : 1, cursor: page === 1 ? 'not-allowed' : 'pointer' }}
              >
                ← Anterior
              </button>
              <span style={{ padding: '4px 12px', fontSize: '12px' }}>Página {page}</span>
              <button
                disabled={page * 25 >= total}
                onClick={() => setPage(page + 1)}
                className="link-btn"
                style={{ opacity: page * 25 >= total ? 0.5 : 1, cursor: page * 25 >= total ? 'not-allowed' : 'pointer' }}
              >
                Siguiente →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
