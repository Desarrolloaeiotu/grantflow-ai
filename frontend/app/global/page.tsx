'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function GlobalPage() {
  const [stats, setStats] = useState({
    organizations: 0,
    contacts: 0,
    tenders: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  async function fetchStats() {
    try {
      const [orgs, contacts, tenders] = await Promise.all([
        fetch(`${API_URL}/api/v1/organizations?size=1`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/contacts?size=1`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/tenders?region=global&size=1`).then(r => r.json()),
      ])

      setStats({
        organizations: orgs.total || 0,
        contacts: contacts.total || 0,
        tenders: tenders.total || 0,
      })
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="section-hd" style={{ marginBottom: '40px' }}>
        <h1>Módulo GLOBAL</h1>
        <p style={{ color: 'var(--muted)', marginTop: '8px', fontSize: '14px' }}>
          Prospección estratégica de organizaciones, contactos y convocatorias internacionales de financiamiento
        </p>
      </div>

      {loading ? (
        <div className="empty-state">Cargando estadísticas...</div>
      ) : (
        <>
          {/* Stats Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '40px' }}>
            <div style={{
              padding: '20px',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-subtle)'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--primary)' }}>
                {stats.organizations}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '8px' }}>
                Organizaciones Aliadas
              </div>
            </div>

            <div style={{
              padding: '20px',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-subtle)'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--go)' }}>
                {stats.contacts}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '8px' }}>
                Contactos Clave
              </div>
            </div>

            <div style={{
              padding: '20px',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-subtle)'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--info)' }}>
                {stats.tenders}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '8px' }}>
                Convocatorias (≥$100M COP)
              </div>
            </div>
          </div>

          {/* Navigation Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '40px' }}>
            {/* Organizations Card */}
            <Link href="/global/organizations" style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '24px',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.borderColor = 'var(--primary)'
                e.currentTarget.style.backgroundColor = 'var(--bg-subtle)'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
              >
                <div style={{ fontSize: '20px', marginBottom: '12px' }}>🏢</div>
                <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
                  Organizaciones
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '16px' }}>
                  {stats.organizations} fundaciones y multilaterales: LEGO, GCC, Fundación Hilton, BID, IADB, Gates
                </p>
                <div style={{ fontSize: '12px', color: 'var(--primary)', fontWeight: 500 }}>
                  Explorar →
                </div>
              </div>
            </Link>

            {/* Convocatorias Card */}
            <Link href="/global/tenders" style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '24px',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.borderColor = 'var(--info)'
                e.currentTarget.style.backgroundColor = 'var(--bg-subtle)'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
              >
                <div style={{ fontSize: '20px', marginBottom: '12px' }}>📋</div>
                <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
                  Convocatorias Activas
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '16px' }}>
                  {stats.tenders} oportunidades internacionales ≥ COP $100M
                </p>
                <div style={{ fontSize: '12px', color: 'var(--info)', fontWeight: 500 }}>
                  Ver todas →
                </div>
              </div>
            </Link>

            {/* Contacts Card */}
            <Link href="/global/contacts" style={{ textDecoration: 'none' }}>
              <div style={{
                padding: '24px',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.borderColor = 'var(--go)'
                e.currentTarget.style.backgroundColor = 'var(--bg-subtle)'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
              >
                <div style={{ fontSize: '20px', marginBottom: '12px' }}>👥</div>
                <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
                  Contactos Clave
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '16px' }}>
                  {stats.contacts} profesionales en roles de partnerships, grants, cooperación e innovación
                </p>
                <div style={{ fontSize: '12px', color: 'var(--go)', fontWeight: 500 }}>
                  Descubrir →
                </div>
              </div>
            </Link>
          </div>

          {/* Sources Section */}
          <div style={{
            padding: '20px',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: '8px',
            borderLeft: '4px solid var(--info)',
            marginBottom: '20px'
          }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
              📊 Fuentes de Datos
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', fontSize: '12px', color: 'var(--muted)' }}>
              <div>
                <strong>Grants.gov</strong><br/>Subsidios federales USA
              </div>
              <div>
                <strong>BID</strong><br/>Banco Interamericano de Desarrollo
              </div>
              <div>
                <strong>ONU Mujeres</strong><br/>Convocatorias internacionales
              </div>
              <div>
                <strong>DevelopmentAid</strong><br/>Oportunidades de cooperación
              </div>
              <div>
                <strong>RSS Feeds</strong><br/>Noticias de organismos internacionales
              </div>
              <div>
                <strong>Instrumentl</strong><br/>Base de datos de fundaciones (premium)
              </div>
            </div>
          </div>

          {/* Financiadores Estratégicos */}
          <div style={{
            padding: '20px',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: '8px',
            borderLeft: '4px solid var(--go)'
          }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
              🎯 Top Financiadores Históricos aeioTU
            </h4>
            <ul style={{ fontSize: '12px', color: 'var(--muted)', lineHeight: '1.8', marginLeft: '20px' }}>
              <li><strong>LEGO Foundation</strong> — Educación inicial, educación de calidad. USD $1.4M histórico</li>
              <li><strong>Grand Challenges Canada</strong> — Innovación en desarrollo. USD $800K histórico</li>
              <li><strong>Fundación Hilton</strong> — Educación y empoderamiento. USD $650K histórico</li>
              <li><strong>BID</strong> — Desarrollo en América Latina. USD $500K+ histórico</li>
              <li><strong>Fundación Cargill</strong> — Educación agrícola y primera infancia. USD $350K histórico</li>
            </ul>
          </div>
        </>
      )}
    </div>
  )
}
