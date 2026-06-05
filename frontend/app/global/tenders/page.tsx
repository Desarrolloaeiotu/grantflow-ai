'use client'

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Tender, ApiListResponse } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function GlobalTendersPage() {
  const router = useRouter()
  const [tenders, setTenders] = useState<Tender[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    decision: undefined as string | undefined,
    days_to_deadline: undefined as number | undefined,
  })

  useEffect(() => {
    fetchTenders()
  }, [page, filters])

  async function fetchTenders() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        region: "global",
        page: page.toString(),
        size: "10",
      })

      if (filters.decision) params.append("decision", filters.decision)
      if (filters.days_to_deadline) params.append("days_to_deadline", filters.days_to_deadline.toString())

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
      const res = await fetch(`${API_URL}/api/v1/tenders/export?region=global`)
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

  const getTenderTypeColor = (type: string | undefined): string => {
    switch (type) {
      case "grant": return "#2196F3"
      case "premio": return "#FF6F00"
      case "evento": return "#9C27B0"
      case "curso": return "#4CAF50"
      default: return "var(--muted)"
    }
  }

  const getDecisionColor = (decision: string | undefined): string => {
    switch (decision) {
      case "go": return "var(--go)"
      case "no_go": return "var(--no-go)"
      case "pending": return "var(--info)"
      default: return "var(--muted)"
    }
  }

  const daysToDeadline = (deadline: string | null | undefined): number | null => {
    if (!deadline) return null
    const d = new Date(deadline)
    const today = new Date()
    const diff = d.getTime() - today.getTime()
    return Math.ceil(diff / (1000 * 3600 * 24))
  }

  const formatCOP = (amount: number | null | undefined): string => {
    if (!amount) return "—"
    if (amount >= 1_000_000_000) return `$${(amount / 1_000_000_000).toFixed(1)}B`
    if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(0)}M`
    return `$${amount.toLocaleString()}`
  }

  return (
    <div className="page">
      <div className="section-hd" style={{ marginBottom: '20px' }}>
        <h2>Convocatorias GLOBAL</h2>
        <p style={{ color: 'var(--muted)', fontSize: '13px', marginTop: '4px' }}>
          {total} oportunidades internacionales ≥ COP $100M
        </p>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <select
          value={filters.decision || ""}
          onChange={(e) => {
            setFilters({ ...filters, decision: e.target.value || undefined })
            setPage(1)
          }}
          style={{
            padding: '8px 12px',
            fontSize: '13px',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            backgroundColor: 'var(--bg)',
          }}
        >
          <option value="">Todas las decisiones</option>
          <option value="go">GO</option>
          <option value="no_go">NO GO</option>
          <option value="pending">PENDING</option>
        </select>

        <select
          value={filters.days_to_deadline || ""}
          onChange={(e) => {
            setFilters({ ...filters, days_to_deadline: e.target.value ? parseInt(e.target.value) : undefined })
            setPage(1)
          }}
          style={{
            padding: '8px 12px',
            fontSize: '13px',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            backgroundColor: 'var(--bg)',
          }}
        >
          <option value="">Todos los plazos</option>
          <option value="30">Próximos 30 días</option>
          <option value="60">Próximos 60 días</option>
          <option value="90">Próximos 90 días</option>
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            {tenders.map((tender) => {
              const days = daysToDeadline(tender.deadline)
              return (
                <div
                  key={tender.id}
                  onClick={() => router.push(`/global/tenders/${tender.id}`)}
                  style={{
                    padding: '20px',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--primary)'
                    ;(e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border)'
                    ;(e.currentTarget as HTMLDivElement).style.boxShadow = 'none'
                  }}
                >
                  {/* Header: Tipo + Decisión */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {tender.tender_type && (
                        <span style={{
                          fontSize: '11px',
                          padding: '4px 8px',
                          backgroundColor: getTenderTypeColor(tender.tender_type),
                          color: 'white',
                          borderRadius: '3px',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                        }}>
                          {tender.tender_type}
                        </span>
                      )}
                    </div>
                    {tender.decision && (
                      <span style={{
                        fontSize: '11px',
                        padding: '4px 8px',
                        backgroundColor: getDecisionColor(tender.decision),
                        color: 'white',
                        borderRadius: '3px',
                        fontWeight: 600,
                      }}>
                        {tender.decision.toUpperCase()}
                      </span>
                    )}
                  </div>

                  {/* Título */}
                  <h3 style={{ fontSize: '16px', fontWeight: 600, margin: '0', color: 'var(--text)' }}>
                    {tender.title}
                  </h3>

                  {/* Financiador */}
                  <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                    <strong>Financiador:</strong> {tender.funder_name || "—"}
                  </div>

                  {/* Descripción */}
                  {tender.description && (
                    <p style={{ fontSize: '12px', color: 'var(--muted)', margin: '0', lineHeight: '1.4' }}>
                      {tender.description.substring(0, 120)}...
                    </p>
                  )}

                  {/* Monto */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                    <div>
                      <strong style={{ color: 'var(--text)' }}>Monto Min:</strong> <span style={{ color: 'var(--muted)' }}>{formatCOP(tender.amount_min_cop)}</span>
                    </div>
                    <div>
                      <strong style={{ color: 'var(--text)' }}>Monto Max:</strong> <span style={{ color: 'var(--muted)' }}>{formatCOP(tender.amount_max_cop)}</span>
                    </div>
                  </div>

                  {/* Deadline */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', padding: '8px 0', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
                    <div>
                      <strong style={{ color: 'var(--text)' }}>Cierre:</strong> <span style={{ color: 'var(--muted)' }}>{tender.deadline ? new Date(tender.deadline).toLocaleDateString() : "—"}</span>
                    </div>
                    {days && (
                      <span style={{ color: days < 30 ? 'var(--no-go)' : days < 60 ? '#FF9800' : 'var(--go)', fontWeight: 600 }}>
                        {days}d
                      </span>
                    )}
                  </div>

                  {/* Score / Recomendación */}
                  {tender.score_total !== null && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
                      <strong style={{ color: 'var(--text)' }}>Afinidad aeioTU:</strong>
                      <div style={{ flex: 1, height: '6px', backgroundColor: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${(tender.score_total / 10) * 100}%`,
                            backgroundColor: tender.score_total >= 7 ? 'var(--go)' : tender.score_total >= 5 ? '#FF9800' : 'var(--no-go)',
                          }}
                        />
                      </div>
                      <span style={{ fontWeight: 600, minWidth: '30px' }}>{tender.score_total}/10</span>
                    </div>
                  )}

                  {/* Links */}
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
                    {tender.url_rfp && (
                      <a
                        href={tender.url_rfp}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          fontSize: '11px',
                          padding: '4px 8px',
                          backgroundColor: 'var(--info)',
                          color: 'white',
                          borderRadius: '3px',
                          textDecoration: 'none',
                          fontWeight: 500,
                        }}
                      >
                        Convocatoria
                      </a>
                    )}
                    {tender.url_form && (
                      <a
                        href={tender.url_form}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          fontSize: '11px',
                          padding: '4px 8px',
                          backgroundColor: 'var(--go)',
                          color: 'white',
                          borderRadius: '3px',
                          textDecoration: 'none',
                          fontWeight: 500,
                        }}
                      >
                        Formulario
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
                disabled={page * 10 >= total}
                onClick={() => setPage(page + 1)}
                className="link-btn"
                style={{ opacity: page * 10 >= total ? 0.5 : 1, cursor: page * 10 >= total ? 'not-allowed' : 'pointer' }}
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
