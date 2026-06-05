'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function NacionalHomePage() {
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
        fetch(`${API_URL}/api/v1/organizations?region=nacional&size=1`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/contacts?size=1`).then(r => r.json()),
        fetch(`${API_URL}/api/v1/tenders?region=nacional&size=1`).then(r => r.json()),
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
        <h1>Módulo NACIONAL - Colombia</h1>
        <p style={{ color: 'var(--muted)', marginTop: '8px', fontSize: '14px' }}>
          Prospección estratégica de financiamiento público y privado en Colombia
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
                Organizaciones Nacionales
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
                Convocatorias (≥$50M COP)
              </div>
            </div>
          </div>

          {/* Navigation Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '40px' }}>
            {/* Organizations Card */}
            <Link href="/nacional/organizations" style={{ textDecoration: 'none' }}>
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
                <div style={{ fontSize: '20px', marginBottom: '12px' }}>🏛️</div>
                <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
                  Organizaciones
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '16px' }}>
                  {stats.organizations} organizaciones colombianas: ICBF, MinEducación, Cajas, Fundaciones
                </p>
                <div style={{ fontSize: '12px', color: 'var(--primary)', fontWeight: 500 }}>
                  Explorar →
                </div>
              </div>
            </Link>

            {/* Tenders Card */}
            <Link href="/nacional/convocatorias" style={{ textDecoration: 'none' }}>
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
                  {stats.tenders} oportunidades colombianas ≥ COP $50M
                </p>
                <div style={{ fontSize: '12px', color: 'var(--info)', fontWeight: 500 }}>
                  Ver todas →
                </div>
              </div>
            </Link>

            {/* Contacts Card */}
            <Link href="/nacional/contacts" style={{ textDecoration: 'none' }}>
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
                  Funcionarios, coordinadores de programas y gerentes de fundaciones locales
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
                <strong>SECOP</strong><br/>Sistema Electrónico de Contratación Pública
              </div>
              <div>
                <strong>ICBF</strong><br/>Instituto Colombiano de Bienestar Familiar
              </div>
              <div>
                <strong>MinEducación</strong><br/>Ministerio de Educación Nacional
              </div>
              <div>
                <strong>Cajas</strong><br/>Fondos de Compensación Familiar
              </div>
              <div>
                <strong>Fundaciones</strong><br/>Fundaciones privadas y empresariales
              </div>
              <div>
                <strong>RSS + News</strong><br/>Feeds de noticias y portales educativos
              </div>
            </div>
          </div>

          {/* Oportunidades Prioritarias */}
          <div style={{
            padding: '20px',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: '8px',
            borderLeft: '4px solid var(--go)'
          }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
              🎯 Oportunidades Prioritarias 2026
            </h4>
            <ul style={{ fontSize: '12px', color: 'var(--muted)', lineHeight: '1.8', marginLeft: '20px' }}>
              <li><strong>O1:</strong> Fortalecimiento de CDI en contextos de vulnerabilidad (MEN + Fondos) — COP $280-450M</li>
              <li><strong>O2:</strong> Programa de formación docente en primera infancia (Cajas) — COP $180-320M</li>
              <li><strong>O3:</strong> Acompañamiento pedagógico a jardines privados y rurales — COP $120-200M</li>
              <li><strong>O4:</strong> Incidencia en política pública de primera infancia (ICBF + MEN) — COP $200-350M</li>
            </ul>
          </div>
        </>
      )}
    </div>
  )
}
