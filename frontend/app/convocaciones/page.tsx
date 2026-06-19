'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Convocation {
  id: string
  title: string
  objective: string
  type: 'grant' | 'premio' | 'evento' | 'curso'
  deadline: string
  open_date: string
  amount_min_cop?: number
  amount_max_cop?: number
  url_convocation: string
  url_tor?: string
  url_form?: string
  organization_website?: string
  source_name: string
  verified: boolean
  data_completeness: number
}

interface ListResponse {
  items: Convocation[]
  total: number
  page: number
  size: number
}

function ScoreBadge({ completeness }: { completeness: number }) {
  const color = completeness >= 80 ? 'var(--go)' : completeness >= 60 ? '#ff9800' : 'var(--nogo)'

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
        {completeness}%
      </div>
    </div>
  )
}

export default function ConvocacionesPage() {
  const [convocations, setConvocations] = useState<Convocation[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    type: '',
    verified_only: false,
    days_to_deadline: '',
    source: ''
  })

  useEffect(() => {
    fetchConvocations()
  }, [page, filters])

  async function fetchConvocations() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: '25'
      })

      if (filters.type) params.append('type', filters.type)
      if (filters.verified_only) params.append('verified_only', 'true')
      if (filters.days_to_deadline) params.append('days_to_deadline', filters.days_to_deadline)
      if (filters.source) params.append('source', filters.source)

      const res = await fetch(`${API_URL}/api/v1/convocations?${params}`)
      if (!res.ok) throw new Error(`API error: ${res.status}`)

      const data: ListResponse = await res.json()
      setConvocations(data.items || [])
      setTotal(data.total || 0)
    } catch (error) {
      console.error('Error fetching convocations:', error)
      setConvocations([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const params = new URLSearchParams()
      if (filters.type) params.append('type', filters.type)
      if (filters.verified_only) params.append('verified_only', 'true')
      if (filters.days_to_deadline) params.append('days_to_deadline', filters.days_to_deadline)

      const res = await fetch(`${API_URL}/api/v1/convocations/export?${params}`)
      if (!res.ok) throw new Error('Export failed')

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `convocaciones-${new Date().toISOString().split('T')[0]}.csv`
      a.click()
    } catch (error) {
      console.error('Error exporting:', error)
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'grant': return '#2196F3'
      case 'premio': return '#FF6F00'
      case 'evento': return '#9C27B0'
      case 'curso': return '#4CAF50'
      default: return '#999'
    }
  }

  const daysUntilDeadline = (deadline: string): number | null => {
    const d = new Date(deadline)
    const today = new Date()
    const diff = d.getTime() - today.getTime()
    return Math.ceil(diff / (1000 * 3600 * 24))
  }

  const formatCOP = (amount: number | null | undefined): string => {
    if (!amount) return '—'
    if (amount >= 1_000_000_000) return `$${(amount / 1_000_000_000).toFixed(1)}B`
    if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(0)}M`
    return `$${amount.toLocaleString()}`
  }

  const formatDate = (dateStr: string): string => {
    try {
      return new Date(dateStr).toLocaleDateString('es-CO', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return '—'
    }
  }

  return (
    <div className="page">
      <div className="section-hd" style={{ marginBottom: '20px' }}>
        <h2>Convocaciones Verificadas</h2>
        <span className="badge-blue" style={{ marginLeft: 'auto' }}>Estructura datos validada</span>
      </div>

      <p style={{ color: 'var(--muted)', fontSize: '13px', marginBottom: '20px' }}>
        {total} convocaciones con campos obligatorios verificados
      </p>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <select
          value={filters.type}
          onChange={(e) => {
            setFilters({ ...filters, type: e.target.value })
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
          <option value="">Todos los tipos</option>
          <option value="grant">Grant</option>
          <option value="premio">Premio</option>
          <option value="evento">Evento</option>
          <option value="curso">Curso</option>
        </select>

        <select
          value={filters.days_to_deadline}
          onChange={(e) => {
            setFilters({ ...filters, days_to_deadline: e.target.value })
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
          <option value="">Todos los plazos</option>
          <option value="7">Próximos 7 días</option>
          <option value="30">Próximos 30 días</option>
          <option value="60">Próximos 60 días</option>
          <option value="90">Próximos 90 días</option>
        </select>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={filters.verified_only}
            onChange={(e) => {
              setFilters({ ...filters, verified_only: e.target.checked })
              setPage(1)
            }}
          />
          Solo verificadas
        </label>

        <button
          onClick={handleExport}
          className="link-btn primary"
          style={{ marginLeft: 'auto' }}
        >
          📥 Exportar CSV
        </button>
      </div>

      {loading ? (
        <div className="empty-state">Cargando convocaciones...</div>
      ) : convocations.length === 0 ? (
        <div className="empty-state">No hay convocaciones que cumplan los criterios</div>
      ) : (
        <>
          <style>{`
            .convocation-card {
              transition: all 0.2s;
            }
            .convocation-card:hover {
              background: var(--bg2);
              border-color: var(--border2);
            }
          `}</style>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
            {convocations.map((conv) => {
              const daysLeft = daysUntilDeadline(conv.deadline)

              return (
                <div key={conv.id} className="convocation-card" style={{
                  background: 'var(--bg)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--r)',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}>
                  {/* Header: Tipo + Completitud */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ fontSize: '14px', fontWeight: 700, margin: '0 0 4px 0', color: 'var(--text)' }}>
                        {conv.title}
                      </h3>
                      <p style={{ fontSize: '11px', color: 'var(--muted)', margin: 0 }}>
                        {conv.source_name.toUpperCase()}
                      </p>
                    </div>
                    <ScoreBadge completeness={conv.data_completeness} />
                  </div>

                  {/* Objetivo */}
                  <p style={{ fontSize: '12px', color: 'var(--muted)', margin: 0, lineHeight: '1.4' }}>
                    {conv.objective && conv.objective.substring(0, 100)}...
                  </p>

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
                      <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '2px' }}>Tipo</div>
                      <div style={{
                        color: 'white',
                        fontWeight: 700,
                        backgroundColor: getTypeColor(conv.type),
                        padding: '2px 4px',
                        borderRadius: '2px',
                        display: 'inline-block',
                        fontSize: '9px',
                        textTransform: 'uppercase'
                      }}>
                        {conv.type}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '2px' }}>Cierre</div>
                      <div style={{ color: 'var(--text)', fontWeight: 700 }}>
                        {formatDate(conv.deadline)}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '2px' }}>Días</div>
                      <div style={{ color: daysLeft && daysLeft <= 7 ? 'var(--nogo)' : 'var(--text)', fontWeight: 700 }}>
                        {daysLeft !== null ? daysLeft + 'd' : '—'}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '2px' }}>Verificada</div>
                      <div style={{ color: conv.verified ? 'var(--go)' : 'var(--muted)', fontWeight: 700 }}>
                        {conv.verified ? '✓ Sí' : '—'}
                      </div>
                    </div>
                  </div>

                  {/* Monto */}
                  {(conv.amount_min_cop || conv.amount_max_cop) && (
                    <div style={{ fontSize: '12px' }}>
                      <div style={{ color: 'var(--muted)', fontWeight: 600, marginBottom: '4px' }}>Monto COP</div>
                      <div style={{ color: 'var(--text)', fontWeight: 700 }}>
                        {formatCOP(conv.amount_min_cop)} - {formatCOP(conv.amount_max_cop)}
                      </div>
                    </div>
                  )}

                  {/* Badges */}
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '4px' }}>
                    {conv.verified && <span className="badge-go" style={{ fontSize: '10px', padding: '4px 6px' }}>✓ VERIFICADA</span>}
                    {daysLeft && daysLeft <= 7 && <span className="badge-nogo" style={{ fontSize: '10px', padding: '4px 6px' }}>URGENTE</span>}
                  </div>

                  {/* Links */}
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {conv.url_convocation && (
                      <a
                        href={conv.url_convocation}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-btn primary"
                        style={{ fontSize: '11px', padding: '6px 8px' }}
                      >
                        Ver convocatoria →
                      </a>
                    )}
                    {conv.url_form && (
                      <a
                        href={conv.url_form}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-btn"
                        style={{ fontSize: '11px', padding: '6px 8px' }}
                      >
                        Formulario
                      </a>
                    )}
                    {conv.url_tor && (
                      <a
                        href={conv.url_tor}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-btn"
                        style={{ fontSize: '11px', padding: '6px 8px' }}
                      >
                        TOR
                      </a>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', fontSize: '12px', color: 'var(--muted)' }}>
            <span>
              Mostrando <strong>{convocations.length}</strong> de <strong>{total}</strong> convocaciones
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
