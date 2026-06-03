'use client'

import { useState, useEffect } from "react"
import { Organization, ApiListResponse } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    invests_colombia: false,
    invests_latam: false,
  })

  useEffect(() => {
    fetchOrganizations()
  }, [page, filters])

  async function fetchOrganizations() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: "25",
      })

      if (filters.invests_colombia) params.append("invests_colombia", "true")
      if (filters.invests_latam) params.append("invests_latam", "true")

      const res = await fetch(`${API_URL}/api/v1/organizations?${params}`)
      const data: ApiListResponse<Organization> = await res.json()

      setOrganizations(data.items)
      setTotal(data.total)
    } catch (error) {
      console.error("Error fetching organizations:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const res = await fetch(`${API_URL}/api/v1/organizations/export/csv`)
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
        <h2>Organizaciones Aliadas</h2>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={filters.invests_colombia}
            onChange={(e) =>
              setFilters({ ...filters, invests_colombia: e.target.checked })
            }
            style={{ cursor: 'pointer' }}
          />
          <span>Invierte en Colombia</span>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={filters.invests_latam}
            onChange={(e) =>
              setFilters({ ...filters, invests_latam: e.target.checked })
            }
            style={{ cursor: 'pointer' }}
          />
          <span>Invierte en LatAm</span>
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
        <div className="empty-state">Cargando organizaciones...</div>
      ) : organizations.length === 0 ? (
        <div className="empty-state">No hay organizaciones que cumplan los criterios</div>
      ) : (
        <>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>País</th>
                  <th>Tipo</th>
                  <th style={{ textAlign: 'center' }}>CO</th>
                  <th style={{ textAlign: 'center' }}>LatAm</th>
                  <th>Rol aeioTU</th>
                  <th>Contactos</th>
                </tr>
              </thead>
              <tbody>
                {organizations.map((org) => (
                  <tr key={org.id}>
                    <td className="td-link" style={{ fontWeight: 500 }}>
                      {org.name}
                    </td>
                    <td className="td-muted">{org.country || "—"}</td>
                    <td className="td-muted">{org.org_type || "—"}</td>
                    <td style={{ textAlign: 'center', color: org.invests_colombia ? 'var(--go)' : 'var(--muted2)', fontWeight: org.invests_colombia ? 600 : 400 }}>
                      {org.invests_colombia ? "✓" : "—"}
                    </td>
                    <td style={{ textAlign: 'center', color: org.invests_latam ? 'var(--go)' : 'var(--muted2)', fontWeight: org.invests_latam ? 600 : 400 }}>
                      {org.invests_latam ? "✓" : "—"}
                    </td>
                    <td><span className="badge-blue">{org.aeiotu_role || "—"}</span></td>
                    <td className="td-muted">{org.contacts?.length || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
