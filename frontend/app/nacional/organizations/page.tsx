'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Organization, ApiListResponse } from '@/app/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function NacionalOrganizationsPage() {
  const router = useRouter()
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    access_type: '' as string,
  })

  useEffect(() => {
    fetchOrganizations()
  }, [page, filters])

  async function fetchOrganizations() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        country: 'Colombia',
        page: page.toString(),
        size: '12',
      })

      if (filters.access_type) params.append('access_type', filters.access_type)

      const res = await fetch(`${API_URL}/api/v1/organizations?${params}`)
      const data: ApiListResponse<Organization> = await res.json()

      setOrganizations(data.items)
      setTotal(data.total)
    } catch (error) {
      console.error('Error fetching organizations:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const res = await fetch(`${API_URL}/api/v1/organizations/export?country=Colombia`)
      const data = await res.json()
      const csv = atob(data.content_base64)
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = data.filename
      a.click()
    } catch (error) {
      console.error('Error exporting:', error)
    }
  }

  const getAccessTypeColor = (access_type: string | undefined): string => {
    switch (access_type) {
      case 'convocatoria': return '#2196F3'
      case 'mixto': return '#FF9800'
      case 'relacional': return '#4CAF50'
      case 'invitacion': return '#9C27B0'
      default: return 'var(--muted)'
    }
  }

  const getStrategicObjColor = (obj: string | undefined): string => {
    switch (obj) {
      case 'capital': return '#1976D2'
      case 'exportacion_modelo': return '#388E3C'
      case 'red': return '#D32F2F'
      default: return 'var(--muted)'
    }
  }

  const getOrgTypeColor = (org_type: string | undefined): string => {
    switch (org_type) {
      case 'Público': return '#1976D2'
      case 'Privado': return '#D32F2F'
      case 'Filantropía': return '#388E3C'
      case 'ONG': return '#F57C00'
      case 'Caja de Compensación': return '#7B1FA2'
      default: return '#757575'
    }
  }

  return (
    <div className="page">
      <div className="section-hd" style={{ marginBottom: '20px' }}>
        <h2>Organizaciones NACIONAL Colombia</h2>
        <p style={{ color: 'var(--muted)', fontSize: '13px', marginTop: '4px' }}>
          {total} organizaciones nacionales: ICBF, MinEducación, Cajas, Fundaciones
        </p>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <select
          value={filters.access_type}
          onChange={(e) => {
            setFilters({ ...filters, access_type: e.target.value })
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
          <option value="">Todos los tipos de acceso</option>
          <option value="convocatoria">Convocatoria Abierta</option>
          <option value="mixto">Mixto (Convocatoria + Relacional)</option>
          <option value="relacional">Relacional</option>
          <option value="invitacion">Por Invitación</option>
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
        <div className="empty-state">Cargando organizaciones...</div>
      ) : organizations.length === 0 ? (
        <div className="empty-state">No hay organizaciones nacionales que cumplan los criterios</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            {organizations.map((org) => (
              <div
                key={org.id}
                onClick={() => router.push(`/nacional/organizations/${org.id}`)}
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 600, margin: '0', color: 'var(--text)', flex: 1 }}>
                    {org.name}
                  </h3>
                  {org.org_type && (
                    <span style={{
                      fontSize: '11px',
                      padding: '4px 8px',
                      backgroundColor: getOrgTypeColor(org.org_type),
                      color: 'white',
                      borderRadius: '3px',
                      fontWeight: 500,
                      whiteSpace: 'nowrap',
                    }}>
                      {org.org_type}
                    </span>
                  )}
                </div>

                <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                  <strong style={{ color: 'var(--text)' }}>🌍 País:</strong> {org.country || '—'}
                </div>

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

                {org.general_objective && (
                  <p style={{ fontSize: '12px', color: 'var(--muted)', margin: '0', lineHeight: '1.4' }}>
                    <strong style={{ color: 'var(--text)' }}>Objetivo:</strong> {org.general_objective}
                  </p>
                )}

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

                {org.aeiotu_role && (
                  <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                    <strong style={{ color: 'var(--text)' }}>Rol con aeioTU:</strong> {org.aeiotu_role}
                  </div>
                )}

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
