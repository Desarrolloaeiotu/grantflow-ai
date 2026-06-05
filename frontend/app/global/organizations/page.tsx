'use client'

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Organization, ApiListResponse } from "@/app/types"
import { FilterSelect } from "@/app/components/FilterSelect"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function GlobalOrganizationsPage() {
  const router = useRouter()
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    invests_colombia: undefined as boolean | undefined,
    invests_latam: undefined as boolean | undefined,
    org_type: undefined as string | undefined,
    strategic_obj: undefined as string | undefined,
    access_type: undefined as string | undefined,
  })

  useEffect(() => {
    fetchOrganizations()
  }, [page, filters])

  async function fetchOrganizations() {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: "12",
      })

      if (filters.invests_colombia !== undefined) params.append("invests_colombia", filters.invests_colombia.toString())
      if (filters.invests_latam !== undefined) params.append("invests_latam", filters.invests_latam.toString())
      if (filters.org_type !== undefined) params.append("org_type", filters.org_type)
      if (filters.strategic_obj !== undefined) params.append("strategic_obj", filters.strategic_obj)
      if (filters.access_type !== undefined) params.append("access_type", filters.access_type)

      const res = await fetch(`${API_URL}/api/v1/organizations?${params}`)

      if (!res.ok) {
        throw new Error(`Fetch failed: ${res.statusText}`)
      }

      const data: ApiListResponse<Organization> = await res.json()

      setOrganizations(data.items)
      setTotal(data.total)
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Error desconocido al cargar organizaciones'
      setError(msg)
      console.error("Error fetching organizations:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/v1/organizations/export/csv`)

      if (!res.ok) {
        throw new Error(`Export failed: ${res.statusText}`)
      }

      const data = await res.json()

      // Validate structure
      if (!data.content_base64 || typeof data.content_base64 !== 'string') {
        throw new Error('Invalid export response structure')
      }

      // Rough size check: base64 is ~4/3 of original
      const estimatedBytes = (data.content_base64.length * 3) / 4
      if (estimatedBytes > 10 * 1024 * 1024) {
        throw new Error('Export file too large (max 10MB)')
      }

      const csv = atob(data.content_base64)
      const blob = new Blob([csv], { type: "text/csv" })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = data.filename || 'organizations.csv'
      a.click()
      window.URL.revokeObjectURL(url)  // Cleanup memory
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Error desconocido al exportar'
      setError(`Export failed: ${msg}`)
      console.error("Error exporting:", error)
    }
  }

  return (
    <div className="page">
      <div className="section-hd" style={{ marginBottom: '20px' }}>
        <h2>Organizaciones Aliadas GLOBAL</h2>
        <p style={{ color: 'var(--muted)', fontSize: '13px', marginTop: '4px' }}>
          {total} organizaciones internacionales con inversión en ECD/Educación inicial
        </p>
      </div>

      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'rgba(211, 47, 47, 0.1)',
          border: '1px solid var(--nogo)',
          borderRadius: '4px',
          color: 'var(--nogo)',
          fontSize: '13px',
          marginBottom: '16px'
        }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={filters.invests_colombia ?? false}
            onChange={(e) => {
              setFilters({ ...filters, invests_colombia: e.target.checked ? true : undefined })
              setPage(1)
            }}
            style={{ cursor: 'pointer' }}
          />
          <span>Invierte en Colombia</span>
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={filters.invests_latam ?? false}
            onChange={(e) => {
              setFilters({ ...filters, invests_latam: e.target.checked ? true : undefined })
              setPage(1)
            }}
            style={{ cursor: 'pointer' }}
          />
          <span>Invierte en Latinoamérica</span>
        </label>

        <FilterSelect
          label="Tipo de Organización"
          ariaLabel="Filtrar por tipo de organización"
          value={filters.org_type}
          options={[
            { value: 'foundation', label: 'Fundación' },
            { value: 'government', label: 'Gobierno' },
            { value: 'multilateral', label: 'Multilateral' },
            { value: 'corporate', label: 'Corporativo' },
            { value: 'ngo', label: 'ONG' },
            { value: 'academic', label: 'Académico' },
          ]}
          onChange={(v) => { setFilters({ ...filters, org_type: v }); setPage(1) }}
          onFocus={(e) => (e.target.style.boxShadow = '0 0 0 2px var(--primary)')}
          onBlur={(e) => (e.target.style.boxShadow = 'none')}
        />

        <FilterSelect
          label="Objetivo Estratégico"
          ariaLabel="Filtrar por objetivo estratégico"
          value={filters.strategic_obj}
          options={[
            { value: 'capital', label: 'Capital' },
            { value: 'exportacion_modelo', label: 'Exportación Modelo' },
            { value: 'red', label: 'Red' },
          ]}
          onChange={(v) => { setFilters({ ...filters, strategic_obj: v }); setPage(1) }}
          onFocus={(e) => (e.target.style.boxShadow = '0 0 0 2px var(--primary)')}
          onBlur={(e) => (e.target.style.boxShadow = 'none')}
        />

        <FilterSelect
          label="Tipo de Acceso"
          ariaLabel="Filtrar por tipo de acceso"
          value={filters.access_type}
          options={[
            { value: 'convocatoria', label: 'Convocatoria' },
            { value: 'mixto', label: 'Mixto' },
            { value: 'relacional', label: 'Relacional' },
            { value: 'invitacion', label: 'Invitación' },
          ]}
          onChange={(v) => { setFilters({ ...filters, access_type: v }); setPage(1) }}
          onFocus={(e) => (e.target.style.boxShadow = '0 0 0 2px var(--primary)')}
          onBlur={(e) => (e.target.style.boxShadow = 'none')}
        />

        <button
          onClick={handleExport}
          className="link-btn primary"
          style={{ marginLeft: 'auto' }}
        >
          📥 Exportar CSV
        </button>
      </div>

      {loading ? (
        <div className="empty-state">Cargando organizaciones...</div>
      ) : organizations.length === 0 ? (
        <div className="empty-state">No hay organizaciones que cumplan los criterios</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            {organizations.map((org) => (
              <div
                key={org.id}
                onClick={() => router.push(`/global/organizations/${org.id}`)}
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
                {/* Header: Nombre + Tipo */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 600, margin: '0', color: 'var(--text)', flex: 1 }}>
                    {org.name}
                  </h3>
                  {org.org_type && (
                    <span style={{
                      fontSize: '11px',
                      padding: '4px 8px',
                      backgroundColor: '#E0E0E0',
                      color: '#333',
                      borderRadius: '3px',
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                    }}>
                      {org.org_type}
                    </span>
                  )}
                </div>

                {/* País */}
                <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                  <strong style={{ color: 'var(--text)' }}>🌍 País:</strong> {org.country || "—"}
                </div>

                {/* Tipo de Acceso */}
                {org.access_type && (
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '12px' }}>
                    <strong style={{ color: 'var(--text)' }}>Acceso:</strong>
                    <span style={{
                      padding: '3px 8px',
                      backgroundColor: getAccessTypeColor(org.access_type),
                      color: 'white',
                      borderRadius: '3px',
                      fontSize: '11px',
                      fontWeight: 600,
                    }}>
                      {org.access_type}
                    </span>
                  </div>
                )}

                {/* Objetivo Estratégico */}
                {org.strategic_obj && (
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '12px' }}>
                    <strong style={{ color: 'var(--text)' }}>Objetivo:</strong>
                    <span style={{
                      padding: '3px 8px',
                      backgroundColor: getStrategicObjColor(org.strategic_obj),
                      color: 'white',
                      borderRadius: '3px',
                      fontSize: '11px',
                      fontWeight: 600,
                    }}>
                      {org.strategic_obj === 'exportacion_modelo' ? 'Exportar Modelo' : org.strategic_obj === 'capital' ? 'Capital' : 'Red'}
                    </span>
                  </div>
                )}

                {/* Objetivo General */}
                {org.general_objective && (
                  <p style={{ fontSize: '12px', color: 'var(--muted)', margin: '0', lineHeight: '1.4' }}>
                    <strong style={{ color: 'var(--text)' }}>Objetivo:</strong> {org.general_objective}
                  </p>
                )}

                {/* Alcance Geográfico */}
                <div style={{ display: 'flex', gap: '16px', fontSize: '12px', padding: '8px 0', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
                  <div>
                    <strong style={{ color: 'var(--text)' }}>Colombia:</strong> <span style={{ color: org.invests_colombia ? 'var(--go)' : 'var(--muted)' }}>
                      {org.invests_colombia ? '✓ Sí' : '✗ No'}
                    </span>
                  </div>
                  <div>
                    <strong style={{ color: 'var(--text)' }}>Latam:</strong> <span style={{ color: org.invests_latam ? 'var(--go)' : 'var(--muted)' }}>
                      {org.invests_latam ? '✓ Sí' : '✗ No'}
                    </span>
                  </div>
                </div>

                {/* Rol aeioTU */}
                {org.aeiotu_role && (
                  <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                    <strong style={{ color: 'var(--text)' }}>Rol con aeioTU:</strong> {org.aeiotu_role}
                  </div>
                )}

                {/* Historial */}
                {org.has_history && (
                  <div style={{
                    padding: '8px',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    border: '1px solid var(--go)',
                    borderRadius: '4px',
                    fontSize: '11px',
                    color: 'var(--go)',
                    fontWeight: 600,
                    textAlign: 'center',
                  }}>
                    ⭐ Financiador histórico de aeioTU
                  </div>
                )}

                {/* Website */}
                {org.website && (
                  <a
                    href={org.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      fontSize: '11px',
                      padding: '6px 12px',
                      backgroundColor: 'var(--info)',
                      color: 'white',
                      borderRadius: '3px',
                      textDecoration: 'none',
                      fontWeight: 500,
                      textAlign: 'center',
                    }}
                  >
                    Visitar Sitio Web →
                  </a>
                )}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', fontSize: '12px', color: 'var(--muted)' }}>
            <span>
              Mostrando <strong>{organizations.length}</strong> de <strong>{total}</strong> organizaciones
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
                disabled={page * 12 >= total}
                onClick={() => setPage(page + 1)}
                className="link-btn"
                style={{ opacity: page * 12 >= total ? 0.5 : 1, cursor: page * 12 >= total ? 'not-allowed' : 'pointer' }}
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

// Color functions - moved outside component to prevent recreation on each render
const getAccessTypeColor = (type: string | undefined): string => {
  switch (type) {
    case "convocatoria": return "#2196F3"
    case "mixto": return "#FF9800"
    case "relacional": return "#4CAF50"
    case "invitacion": return "#9C27B0"
    default: return "var(--muted)"
  }
}

const getStrategicObjColor = (obj: string | undefined): string => {
  switch (obj) {
    case "capital": return "#1976D2"
    case "exportacion_modelo": return "#388E3C"
    case "red": return "#D32F2F"
    default: return "var(--muted)"
  }
}

const getOrgTypeColor = (org_type: string | undefined): string => {
  switch (org_type) {
    case "foundation": return "#1976D2"
    case "government": return "#D32F2F"
    case "multilateral": return "#388E3C"
    case "corporate": return "#FF9800"
    case "ngo": return "#9C27B0"
    case "academic": return "#00BCD4"
    default: return "var(--muted)"
  }
}
