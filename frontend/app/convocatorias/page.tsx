'use client'

import { useState, useEffect } from "react"
import { Tender, ApiListResponse, formatCOP, formatDate, daysUntilDeadline, getUrgencyLabel, getUrgencyColor } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ConvocatoriasGlobalPage() {
  const [tenders, setTenders] = useState<Tender[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [decision, setDecision] = useState<string>("")

  useEffect(() => {
    fetchTenders()
  }, [page, decision])

  async function fetchTenders() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: "25",
        region: "global",
      })

      if (decision) params.append("decision", decision)

      const res = await fetch(`${API_URL}/api/v1/tenders?${params}`)
      const data: ApiListResponse<Tender> = await res.json()

      setTenders(data.items)
      setTotal(data.total)
    } catch (error) {
      console.error("Error fetching tenders:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const res = await fetch(`${API_URL}/api/v1/tenders/export/csv?region=global`)
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
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '14px', marginBottom: '24px' }}>
            {tenders.map((tender) => {
              const daysLeft = daysUntilDeadline(tender.deadline)
              const urgency = getUrgencyLabel(daysLeft)

              return (
                <div key={tender.id} className="opp-card go-card">
                  <div className="opp-top">
                    <div>
                      <h3 className="opp-title">{tender.title}</h3>
                      <p style={{ fontSize: '12px', color: 'var(--muted2)', marginTop: '4px' }}>
                        <strong>{tender.funder_name || "—"}</strong>
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexShrink: 0, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      {tender.decision === 'go' && <span className="badge-go">✓ GO</span>}
                      {tender.decision === 'no_go' && <span className="badge-nogo">✗ NO GO</span>}
                      {tender.decision === 'pending' && <span className="badge-warn">⏳ PENDING</span>}
                      {tender.deadline && (
                        <span className={daysLeft && daysLeft <= 7 ? 'badge-nogo' : daysLeft && daysLeft <= 15 ? 'badge-warn' : 'badge-muted'}>
                          {urgency}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="opp-meta" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', margin: '12px 0' }}>
                    <div>
                      <div className="kpi-label">Monto máximo</div>
                      <div className="opp-amount">{formatCOP(tender.amount_max_cop)}</div>
                    </div>
                    <div>
                      <div className="kpi-label">Apertura</div>
                      <div style={{ fontSize: '12px', color: 'var(--text)', fontWeight: 500 }}>{formatDate(tender.open_date) || "—"}</div>
                    </div>
                    <div>
                      <div className="kpi-label">Cierre</div>
                      <div style={{ fontSize: '12px', color: 'var(--text)', fontWeight: 500 }}>{formatDate(tender.deadline) || "—"}</div>
                    </div>
                    <div>
                      <div className="kpi-label">Días restantes</div>
                      <div style={{ fontSize: '12px', color: 'var(--text)', fontWeight: 500 }}>{daysLeft !== null ? daysLeft + 'd' : "—"}</div>
                    </div>
                  </div>

                  {tender.description && (
                    <p style={{ fontSize: '12px', color: 'var(--muted2)', lineHeight: 1.5, marginBottom: '12px', borderLeft: '2px solid var(--border2)', paddingLeft: '10px' }}>
                      {tender.description.length > 150 ? tender.description.slice(0, 150) + '...' : tender.description}
                    </p>
                  )}

                  <div className="opp-links">
                    {tender.url_rfp && (
                      <a
                        href={tender.url_rfp}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-btn"
                      >
                        📄 RFP
                      </a>
                    )}
                    {tender.url_tor && (
                      <a
                        href={tender.url_tor}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-btn"
                      >
                        📋 ToR
                      </a>
                    )}
                    {tender.url_form && (
                      <a
                        href={tender.url_form}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-btn"
                      >
                        ✍️ Formulario
                      </a>
                    )}
                  </div>
                </div>
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
