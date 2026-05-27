'use client'

import { useState } from 'react'
import { Contact, FilterState } from '../types'
import FilterBar from './shared/FilterBar'
import { marcarContactado } from '../actions/nacional-actions'

interface ContactosSectionProps {
  contacts: Contact[]
}

export default function ContactosSection({
  contacts,
}: ContactosSectionProps) {
  const [filters, setFilters] = useState<FilterState>({
    estado: '',
    urgencia: '',
    financiador: '',
    sector: '',
  })

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  // Group contacts by funder
  const byFunder = contacts.reduce(
    (acc, contact) => {
      if (!acc[contact.funder_name]) {
        acc[contact.funder_name] = []
      }
      acc[contact.funder_name].push(contact)
      return acc
    },
    {} as Record<string, Contact[]>
  )

  const financiadores = Object.keys(byFunder)
  const sectores = ['Educación privada', 'Tercer sector', 'Gobierno', 'Otros']

  // Apply funder filter
  const filteredFunders = filters.financiador
    ? { [filters.financiador]: byFunder[filters.financiador] || [] }
    : byFunder

  return (
    <div className="page">
      <div className="section-hd">
        <h2>Contactos</h2>
      </div>

      <FilterBar
        activeFilters={filters}
        onFilterChange={handleFilterChange}
        financiadores={financiadores}
        sectores={sectores}
      />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {Object.entries(filteredFunders).map(([funderName, funderContacts]) => (
          <div key={funderName} style={{ padding: '16px 20px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r)' }}>
            <div className="section-hd" style={{ marginBottom: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 500 }}>{funderName}</h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {funderContacts.map((contact) => (
                <ContactRow
                  key={contact.id}
                  contact={contact}
                  onContactado={marcarContactado}
                />
              ))}
            </div>
          </div>
        ))}

        {Object.keys(filteredFunders).length === 0 && (
          <div className="empty-state">
            No hay contactos para los filtros seleccionados
          </div>
        )}
      </div>
    </div>
  )
}

interface ContactRowProps {
  contact: Contact
  onContactado: (
    id: string,
    type: 'llamada' | 'email' | 'reunion',
    note?: string
  ) => Promise<{ success: boolean; error?: string }>
}

function ContactRow({ contact, onContactado }: ContactRowProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [tipoInteraccion, setTipoInteraccion] = useState<'llamada' | 'email' | 'reunion'>('email')

  const handleMarcar = async () => {
    setIsLoading(true)
    try {
      await onContactado(contact.id, tipoInteraccion)
      // Reset form
      setTipoInteraccion('email')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ padding: 12, background: 'var(--bg3)', borderRadius: 'var(--r)', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <h3 style={{ fontWeight: 600, color: 'var(--text)' }}>{contact.full_name}</h3>
          <p style={{ fontSize: 12, color: 'var(--muted)' }}>{contact.title}</p>
        </div>
        {contact.email_verified && (
          <span style={{ display: 'inline-flex', alignItems: 'center', padding: '4px 8px', borderRadius: '999px', fontSize: 11, fontWeight: 500, background: 'var(--go-bg)', color: 'var(--go)' }}>
            ✓ Verificado
          </span>
        )}
      </div>

      <div style={{ marginBottom: 12, fontSize: 12 }}>
        <p style={{ color: 'var(--text)' }}>
          <span style={{ fontWeight: 600 }}>Email:</span> {contact.email}
        </p>
        {contact.linkedin_url && (
          <p style={{ color: 'var(--blue)', textDecoration: 'underline' }}>
            <a href={contact.linkedin_url} target="_blank" rel="noopener noreferrer">
              LinkedIn
            </a>
          </p>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <select
          disabled={isLoading}
          value={tipoInteraccion}
          onChange={(e) =>
            setTipoInteraccion(e.target.value as 'llamada' | 'email' | 'reunion')
          }
          style={{
            padding: '5px 8px',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r)',
            fontSize: 12,
            background: 'var(--bg2)',
            color: 'var(--text)',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            opacity: isLoading ? 0.6 : 1,
          }}
        >
          <option value="email">Email</option>
          <option value="llamada">Llamada</option>
          <option value="reunion">Reunión</option>
        </select>
        <button
          disabled={isLoading}
          onClick={handleMarcar}
          className="link-btn primary"
          style={{
            padding: '5px 12px',
            fontSize: 12,
            cursor: isLoading ? 'not-allowed' : 'pointer',
            opacity: isLoading ? 0.6 : 1,
          }}
        >
          {isLoading ? '...' : 'Marcar contactado'}
        </button>
      </div>
    </div>
  )
}
