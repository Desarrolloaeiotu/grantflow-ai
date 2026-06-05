'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Tender, formatCOP, daysUntilDeadline } from '@/app/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Contact {
  id: string
  full_name: string
  last_name?: string
  title?: string
  email?: string
  linkedin_url?: string
  role_category?: string
}

export default function NacionalTenderDetailPage() {
  const params = useParams()
  const id = (params?.id as string) || ''

  const [tender, setTender] = useState<Tender | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    fetchData()
  }, [id])

  async function fetchData() {
    try {
      const res = await fetch(`${API_URL}/api/v1/tenders/${id}`)
      if (!res.ok) throw new Error('Convocatoria no encontrada')
      const tenderData = await res.json()
      setTender(tenderData)

      // Fetch contacts if we have a funder_id
      if (tenderData.funder_id) {
        const contactsRes = await fetch(`${API_URL}/api/v1/contacts?funder_id=${tenderData.funder_id}&size=50`)
        if (contactsRes.ok) {
          const contactsData = await contactsRes.json()
          const sorted = (contactsData.items || []).sort((a: Contact, b: Contact) => {
            const priority = { partnerships: 0, grants: 1, cooperation: 2, innovation: 3, development: 4 }
            const aPriority = priority[a.role_category as keyof typeof priority] ?? 999
            const bPriority = priority[b.role_category as keyof typeof priority] ?? 999
            return aPriority - bPriority
          })
          setContacts(sorted)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="page" style={{ textAlign: 'center', padding: '40px' }}>Cargando...</div>
  if (error || !tender) return <div className="page" style={{ textAlign: 'center', padding: '40px', color: 'var(--nogo)' }}>Error: {error}</div>

  const daysLeft = daysUntilDeadline(tender.deadline)
  const getTenderTypeColor = (type: string | undefined): string => {
    switch (type) {
      case 'grant': return '#2196F3'
      case 'premio': return '#FF6F00'
      case 'evento': return '#9C27B0'
      case 'curso': return '#4CAF50'
      default: return 'var(--muted)'
    }
  }

  const getDecisionColor = (decision: string | undefined): string => {
    switch (decision) {
      case 'go': return 'var(--go)'
      case 'no_go': return 'var(--no-go)'
      case 'pending': return 'var(--info)'
      default: return 'var(--muted)'
    }
  }

  return (
    <div className="page">
      <Link href="/nacional/convocatorias" style={{ color: 'var(--primary)', textDecoration: 'none', fontSize: '12px', marginBottom: '16px', display: 'inline-block' }}>
        ← Volver a Convocatorias
      </Link>

      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '20px' }}>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: '24px', fontWeight: 700, margin: '0 0 12px 0', color: 'var(--text)' }}>{tender.title}</h1>
            <p style={{ fontSize: '12px', color: 'var(--muted)', margin: 0 }}><strong>Financiador:</strong> {tender.funder_name || '—'}</p>
          </div>
        </div>
      </div>

      {tender.description && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase' }}>Descripción</div>
          <p style={{ fontSize: '13px', color: 'var(--text)', margin: 0, lineHeight: '1.5' }}>{tender.description}</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase' }}>Monto Min</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text)', fontFamily: 'monospace' }}>{formatCOP(tender.amount_min_cop)}</div>
        </div>
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase' }}>Monto Max</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text)', fontFamily: 'monospace' }}>{formatCOP(tender.amount_max_cop)}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase' }}>Cierre</div>
          <div style={{ fontSize: '13px', color: 'var(--text)', fontWeight: 500 }}>{tender.deadline ? new Date(tender.deadline).toLocaleDateString('es-CO') : '—'}</div>
          {daysLeft && <div style={{ fontSize: '12px', color: daysLeft < 30 ? 'var(--no-go)' : 'var(--go)', marginTop: '4px', fontWeight: 600 }}>{daysLeft}d</div>}
        </div>
      </div>

      {tender.score_total !== null && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '12px', textTransform: 'uppercase' }}>Afinidad aeioTU</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: tender.score_total >= 7 ? 'var(--go)' : tender.score_total >= 5 ? '#FF9800' : 'var(--no-go)', fontFamily: 'monospace' }}>{tender.score_total}/10</div>
        </div>
      )}

      {/* Contactos Clave */}
      {contacts.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)', marginBottom: '12px', textTransform: 'uppercase' }}>
            Contactos Clave
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
            {contacts.map((contact) => (
              <div key={contact.id} style={{
                background: 'var(--bg2)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '12px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '12px', marginBottom: '8px' }}>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
                      {contact.full_name} {contact.last_name ? contact.last_name : ''}
                    </div>
                    {contact.title && (
                      <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
                        {contact.title}
                      </div>
                    )}
                  </div>
                  {contact.role_category && (
                    <span style={{
                      fontSize: '10px',
                      padding: '3px 8px',
                      backgroundColor: contact.role_category === 'partnerships' ? '#4CAF50' :
                                      contact.role_category === 'grants' ? '#2196F3' :
                                      contact.role_category === 'cooperation' ? '#FF9800' :
                                      contact.role_category === 'innovation' ? '#9C27B0' :
                                      contact.role_category === 'development' ? '#F44336' : '#757575',
                      color: 'white',
                      borderRadius: '3px',
                      fontWeight: 500,
                      whiteSpace: 'nowrap'
                    }}>
                      {contact.role_category}
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '12px', fontSize: '11px', flexWrap: 'wrap' }}>
                  {contact.email && (
                    <a href={`mailto:${contact.email}`} style={{ color: 'var(--primary)', textDecoration: 'none' }}>
                      ✉️ {contact.email}
                    </a>
                  )}
                  {contact.linkedin_url && (
                    <a href={contact.linkedin_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)', textDecoration: 'none' }}>
                      💼 LinkedIn
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(tender.url_rfp || tender.url_form) && (
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {tender.url_rfp && <a href={tender.url_rfp} target="_blank" rel="noopener noreferrer" style={{ padding: '10px 16px', backgroundColor: 'var(--info)', color: 'white', borderRadius: '4px', textDecoration: 'none', fontSize: '12px', fontWeight: 500 }}>Ver Convocatoria →</a>}
          {tender.url_form && <a href={tender.url_form} target="_blank" rel="noopener noreferrer" style={{ padding: '10px 16px', backgroundColor: 'var(--go)', color: 'white', borderRadius: '4px', textDecoration: 'none', fontSize: '12px', fontWeight: 500 }}>Formulario →</a>}
        </div>
      )}
    </div>
  )
}
