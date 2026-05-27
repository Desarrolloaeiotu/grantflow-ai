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
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Contactos</h1>

      <FilterBar
        activeFilters={filters}
        onFilterChange={handleFilterChange}
        financiadores={financiadores}
        sectores={sectores}
      />

      <div className="space-y-6">
        {Object.entries(filteredFunders).map(([funderName, funderContacts]) => (
          <div key={funderName} className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {funderName}
            </h2>

            <div className="space-y-4">
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
          <div className="p-8 text-center text-gray-600">
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
    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{contact.full_name}</h3>
          <p className="text-sm text-gray-600">{contact.title}</p>
        </div>
        {contact.email_verified && (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✓ Verificado
          </span>
        )}
      </div>

      <div className="mb-3 text-sm">
        <p className="text-gray-700">
          <span className="font-semibold">Email:</span> {contact.email}
        </p>
        {contact.linkedin_url && (
          <p className="text-blue-600 hover:underline">
            <a href={contact.linkedin_url} target="_blank" rel="noopener noreferrer">
              LinkedIn
            </a>
          </p>
        )}
      </div>

      <div className="flex gap-2">
        <select
          disabled={isLoading}
          value={tipoInteraccion}
          onChange={(e) =>
            setTipoInteraccion(e.target.value as 'llamada' | 'email' | 'reunion')
          }
          className="px-2 py-1 border border-gray-300 rounded text-xs"
        >
          <option value="email">Email</option>
          <option value="llamada">Llamada</option>
          <option value="reunion">Reunión</option>
        </select>
        <button
          disabled={isLoading}
          onClick={handleMarcar}
          className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 disabled:bg-gray-400"
        >
          {isLoading ? '...' : 'Marcar contactado'}
        </button>
      </div>
    </div>
  )
}
