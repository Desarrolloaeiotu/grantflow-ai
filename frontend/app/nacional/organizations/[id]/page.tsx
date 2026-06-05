'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Organization } from '@/app/types'

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

export default function OrganizationDetailPage() {
  const params = useParams()
  const id = (params?.id as string) || ''

  const [org, setOrg] = useState<Organization | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    fetchData()
  }, [id])

  async function fetchData() {
    try {
      const [orgRes, contactsRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/organizations/${id}`),
        fetch(`${API_URL}/api/v1/contacts?funder_id=${id}&size=50`)
      ])

      if (!orgRes.ok) throw new Error('Organización no encontrada')
      const orgData = await orgRes.json()
      setOrg(orgData)

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="page" style={{ textAlign: 'center', padding: '40px' }}>Cargando...</div>
  if (error || !org) return <div className="page" style={{ textAlign: 'center', padding: '40px', color: 'var(--nogo)' }}>Error: {error}</div>

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

  return (
    <div className="page">
      {/* Header */}
      <div style={{ marginBottom: '30px' }}>
        <Link href="/nacional/organizations" style={{ color: 'var(--primary)', textDecoration: 'none', fontSize: '12px', marginBottom: '16px', display: 'inline-block' }}>
          ← Volver a Organizaciones
        </Link>

        <div style={{
          background: 'var(--bg2)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '24px',
          marginTop: '16px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: '20px' }}>
            <div style={{ flex: 1 }}>
              <h1 style={{ fontSize: '24px', fontWeight: 700, margin: '0 0 12px 0', color: 'var(--text)' }}>
                {org.name}
              </h1>
              <p style={{ fontSize: '12px', color: 'var(--muted)', margin: 0 }}>
                {org.country}
              </p>
            </div>
            {org.org_type && (
              <span style={{
                fontSize: '11px',
                padding: '6px 12px',
                backgroundColor: getOrgTypeColor(org.org_type),
                color: 'white',
                borderRadius: '4px',
                fontWeight: 500,
                whiteSpace: 'nowrap',
              }}>
                {org.org_type}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Información General */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        {/* Tipo de Acceso */}
        {org.access_type && (
          <div style={{
            background: 'var(--bg2)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase' }}>
              Tipo de Acceso
            </div>
            <span style={{
              padding: '6px 12px',
              backgroundColor: getAccessTypeColor(org.access_type),
              color: 'white',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 600,
              display: 'inline-block'
            }}>
              {org.access_type === 'convocatoria' ? 'Convocatoria Abierta' : org.access_type === 'mixto' ? 'Mixto' : org.access_type === 'relacional' ? 'Relacional' : 'Por Invitación'}
            </span>
          </div>
        )}

        {/* Objetivo Estratégico */}
        {org.strategic_obj && (
          <div style={{
            background: 'var(--bg2)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase' }}>
              Objetivo Estratégico
            </div>
            <span style={{
              padding: '6px 12px',
              backgroundColor: getStrategicObjColor(org.strategic_obj),
              color: 'white',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 600,
              display: 'inline-block'
            }}>
              {org.strategic_obj === 'exportacion_modelo' ? 'Exportar Modelo' : org.strategic_obj === 'capital' ? 'Capital' : 'Red'}
            </span>
          </div>
        )}
      </div>

      {/* Objetivo General */}
      {org.general_objective && (
        <div style={{
          background: 'var(--bg2)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '24px'
        }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase' }}>
            Objetivo General
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text)', margin: 0, lineHeight: '1.5' }}>
            {org.general_objective}
          </p>
        </div>
      )}

      {/* Alcance Geográfico */}
      <div style={{
        background: 'var(--bg2)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '24px'
      }}>
        <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '12px', textTransform: 'uppercase' }}>
          Alcance Geográfico
        </div>
        <div style={{ display: 'flex', gap: '24px', fontSize: '13px' }}>
          <div>
            <strong style={{ color: 'var(--text)' }}>Invierte en Colombia:</strong>{' '}
            <span style={{ color: org.invests_colombia ? 'var(--go)' : 'var(--muted)' }}>
              {org.invests_colombia ? '✓ Sí' : '✗ No'}
            </span>
          </div>
          <div>
            <strong style={{ color: 'var(--text)' }}>Invierte en Latinoamérica:</strong>{' '}
            <span style={{ color: org.invests_latam ? 'var(--go)' : 'var(--muted)' }}>
              {org.invests_latam ? '✓ Sí' : '✗ No'}
            </span>
          </div>
        </div>
      </div>

      {/* Rol con aeioTU */}
      {org.aeiotu_role && (
        <div style={{
          background: 'var(--bg2)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '24px'
        }}>
          <div style={{ fontSize: '10px', color: 'var(--muted)', fontWeight: 600, marginBottom: '8px', textTransform: 'uppercase' }}>
            Rol con aeioTU
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text)', margin: 0 }}>
            {org.aeiotu_role}
          </p>
        </div>
      )}

      {/* Historial */}
      {org.has_history && (
        <div style={{
          background: 'rgba(76, 175, 80, 0.1)',
          border: '1px solid var(--go)',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '24px'
        }}>
          <div style={{ fontSize: '12px', color: 'var(--go)', fontWeight: 600, textAlign: 'center' }}>
            ⭐ Financiador Histórico de aeioTU
          </div>
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

      {/* Enlaces */}
      {(org.website || org.created_at) && (
        <div style={{
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap',
          marginTop: '24px'
        }}>
          {org.website && (
            <a
              href={org.website}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                padding: '10px 16px',
                backgroundColor: 'var(--primary)',
                color: 'white',
                borderRadius: '4px',
                textDecoration: 'none',
                fontSize: '12px',
                fontWeight: 500,
              }}
            >
              Visitar Sitio Web →
            </a>
          )}
        </div>
      )}
    </div>
  )
}
