'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Contact {
  id: string
  full_name: string
  last_name?: string
  title?: string
  email?: string
  linkedin_url?: string
  role_category?: string
  priority_score?: number
}

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
  organization_id?: string
  source_name: string
  verified: boolean
  data_completeness: number
  detected_at: string
}

export default function ConvocationDetailPage() {
  const params = useParams()
  const id = params?.id as string

  const [convocation, setConvocation] = useState<Convocation | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    fetchConvocationDetail()
  }, [id])

  async function fetchConvocationDetail() {
    setLoading(true)
    setError(null)
    try {
      // Fetch convocation detail
      const convRes = await fetch(`${API_URL}/api/v1/convocations/${id}`)
      if (!convRes.ok) throw new Error('Convocatoria no encontrada')

      const conv: Convocation = await convRes.json()
      setConvocation(conv)

      // Fetch contacts for organization if organization_id exists
      if (conv.organization_id) {
        try {
          const contactRes = await fetch(
            `${API_URL}/api/v1/contacts?funder_id=${conv.organization_id}&priority_min=1`
          )
          if (contactRes.ok) {
            const contactData = await contactRes.json()
            setContacts(contactData.items || [])
          }
        } catch (err) {
          console.error('Error fetching contacts:', err)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar la convocatoria')
    } finally {
      setLoading(false)
    }
  }

  const formatCOP = (amount: number | null | undefined): string => {
    if (!amount) return '—'
    if (amount >= 1_000_000_000) return `COP $${(amount / 1_000_000_000).toFixed(1)}B`
    if (amount >= 1_000_000) return `COP $${(amount / 1_000_000).toFixed(0)}M`
    return `COP $${amount.toLocaleString()}`
  }

  const formatDate = (dateStr: string): string => {
    try {
      return new Date(dateStr).toLocaleDateString('es-CO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch {
      return '—'
    }
  }

  const daysUntilDeadline = (deadline: string): number | null => {
    const d = new Date(deadline)
    const today = new Date()
    const diff = d.getTime() - today.getTime()
    return Math.ceil(diff / (1000 * 3600 * 24))
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

  const getRoleBadgeColor = (role?: string) => {
    if (!role) return '#ccc'
    if (role.includes('partnership') || role.includes('alliance')) return '#00897b'
    if (role.includes('grant') || role.includes('philanthropy')) return '#1976d2'
    if (role.includes('innovation') || role.includes('ecosystem')) return '#d32f2f'
    if (role.includes('development') || role.includes('program')) return '#7b1fa2'
    if (role.includes('cooperation')) return '#f57c00'
    return '#616161'
  }

  if (loading) {
    return <div className="page"><div className="empty-state">Cargando convocatoria...</div></div>
  }

  if (error || !convocation) {
    return (
      <div className="page">
        <div className="empty-state">
          {error || 'Convocatoria no encontrada'}
        </div>
      </div>
    )
  }

  const daysLeft = daysUntilDeadline(convocation.deadline)

  return (
    <div className="page">
      {/* Header */}
      <div style={{ marginBottom: '24px', borderBottom: '1px solid var(--border)', paddingBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', marginBottom: '12px' }}>
          <div style={{ flex: 1 }}>
            <h1 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: 700 }}>
              {convocation.title}
            </h1>
            <p style={{ margin: 0, color: 'var(--muted)', fontSize: '13px' }}>
              {convocation.source_name.toUpperCase()} • Detectado {formatDate(convocation.detected_at)}
            </p>
          </div>
          <div style={{
            background: getTypeColor(convocation.type),
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontWeight: 700,
            fontSize: '13px',
            textTransform: 'uppercase'
          }}>
            {convocation.type}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '12px' }}>
          {convocation.verified && (
            <span className="badge-go" style={{ fontSize: '12px', padding: '4px 8px' }}>
              ✓ VERIFICADA
            </span>
          )}
          {daysLeft && daysLeft <= 7 && (
            <span className="badge-nogo" style={{ fontSize: '12px', padding: '4px 8px' }}>
              🔴 URGENTE ({daysLeft} días)
            </span>
          )}
          <span style={{
            background: 'var(--bg2)',
            padding: '4px 8px',
            borderRadius: '3px',
            fontSize: '12px',
            color: 'var(--muted)'
          }}>
            Completitud: {convocation.data_completeness}%
          </span>
        </div>
      </div>

      {/* Main Content Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Left: Descripción y Detalles */}
        <div>
          {/* Objetivo */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '8px' }}>
              Objetivo de la convocatoria
            </h3>
            <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text)', margin: 0 }}>
              {convocation.objective}
            </p>
          </div>

          {/* Fechas y Plazos */}
          <div style={{ background: 'var(--bg2)', padding: '16px', borderRadius: '6px', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '12px', margin: '0 0 12px 0' }}>
              Fechas y plazos
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 600, marginBottom: '4px' }}>Fecha de apertura</div>
                <div style={{ fontSize: '14px', fontWeight: 700 }}>{formatDate(convocation.open_date)}</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 600, marginBottom: '4px' }}>Fecha de cierre</div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: daysLeft && daysLeft <= 7 ? 'var(--nogo)' : 'var(--text)' }}>
                  {formatDate(convocation.deadline)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 600, marginBottom: '4px' }}>Días disponibles</div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: daysLeft && daysLeft <= 7 ? 'var(--nogo)' : 'var(--go)' }}>
                  {daysLeft !== null ? `${daysLeft} días` : '—'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 600, marginBottom: '4px' }}>Tipo de financiamiento</div>
                <div style={{ fontSize: '14px', fontWeight: 700, textTransform: 'capitalize' }}>{convocation.type}</div>
              </div>
            </div>
          </div>

          {/* Monto */}
          {(convocation.amount_min_cop || convocation.amount_max_cop) && (
            <div style={{ background: 'var(--bg2)', padding: '16px', borderRadius: '6px', marginBottom: '24px' }}>
              <h3 style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', margin: '0 0 12px 0' }}>
                Montos disponibles
              </h3>
              <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--go)' }}>
                {formatCOP(convocation.amount_min_cop)} — {formatCOP(convocation.amount_max_cop)}
              </div>
            </div>
          )}

          {/* Links */}
          <div style={{ background: 'var(--bg2)', padding: '16px', borderRadius: '6px', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', margin: '0 0 12px 0' }}>
              Documentos y formularios
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {convocation.url_convocation && (
                <a
                  href={convocation.url_convocation}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn primary"
                  style={{ fontSize: '13px', padding: '8px 12px', display: 'inline-block' }}
                >
                  📄 Ver convocatoria oficial
                </a>
              )}
              {convocation.url_tor && (
                <a
                  href={convocation.url_tor}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                  style={{ fontSize: '13px', padding: '8px 12px', display: 'inline-block' }}
                >
                  📋 Términos de referencia (TOR)
                </a>
              )}
              {convocation.url_form && (
                <a
                  href={convocation.url_form}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                  style={{ fontSize: '13px', padding: '8px 12px', display: 'inline-block' }}
                >
                  📝 Formulario de aplicación
                </a>
              )}
              {convocation.organization_website && (
                <a
                  href={convocation.organization_website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                  style={{ fontSize: '13px', padding: '8px 12px', display: 'inline-block' }}
                >
                  🌐 Sitio web de la organización
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar: Contactos */}
        <div>
          <h3 style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '12px' }}>
            Contactos clave
          </h3>

          {contacts.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {contacts.map((contact) => (
                <div
                  key={contact.id}
                  style={{
                    background: 'var(--bg2)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}
                >
                  {/* Nombre */}
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text)' }}>
                      {contact.full_name}{contact.last_name && ` ${contact.last_name}`}
                    </div>
                  </div>

                  {/* Rol */}
                  {contact.title && (
                    <div>
                      <div style={{
                        fontSize: '11px',
                        fontWeight: 600,
                        color: 'white',
                        background: getRoleBadgeColor(contact.role_category),
                        display: 'inline-block',
                        padding: '3px 6px',
                        borderRadius: '3px'
                      }}>
                        {contact.title}
                      </div>
                    </div>
                  )}

                  {/* Rol Categoría */}
                  {contact.role_category && (
                    <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                      Categoría: <strong style={{ textTransform: 'capitalize' }}>{contact.role_category}</strong>
                    </div>
                  )}

                  {/* Priority Score */}
                  {contact.priority_score && (
                    <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                      Relevancia: <strong>{'⭐'.repeat(contact.priority_score)}</strong>
                    </div>
                  )}

                  {/* Email */}
                  {contact.email && (
                    <div style={{ fontSize: '11px', marginTop: '4px' }}>
                      <a
                        href={`mailto:${contact.email}`}
                        style={{ color: 'var(--go)', textDecoration: 'none', fontWeight: 600 }}
                      >
                        ✉️ {contact.email}
                      </a>
                    </div>
                  )}

                  {/* LinkedIn */}
                  {contact.linkedin_url && (
                    <div style={{ fontSize: '11px' }}>
                      <a
                        href={contact.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: 'var(--go)', textDecoration: 'none', fontWeight: 600 }}
                      >
                        in LinkedIn →
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              background: 'var(--bg2)',
              padding: '16px',
              borderRadius: '6px',
              color: 'var(--muted)',
              fontSize: '12px',
              textAlign: 'center'
            }}>
              No hay contactos disponibles para esta organización
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{
        borderTop: '1px solid var(--border)',
        paddingTop: '16px',
        fontSize: '11px',
        color: 'var(--muted)'
      }}>
        <p>
          <strong>Fuente:</strong> {convocation.source_name} |
          <strong style={{ marginLeft: '8px' }}>Detectado:</strong> {formatDate(convocation.detected_at)} |
          <strong style={{ marginLeft: '8px' }}>Verificación:</strong> {convocation.verified ? '✓ Sí' : 'No'}
        </p>
      </div>
    </div>
  )
}
