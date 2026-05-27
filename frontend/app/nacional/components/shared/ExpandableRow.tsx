'use client'

import { useState } from 'react'
import { Opportunity } from '../../types'

interface ExpandableRowProps {
  opportunity: Opportunity
  onStateChange: (newState: string) => Promise<void>
  onAddNote: (note: string) => Promise<void>
}

export default function ExpandableRow({
  opportunity,
  onStateChange,
  onAddNote,
}: ExpandableRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [noteText, setNoteText] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleStateChange = async (newState: string) => {
    if (!newState) return
    setIsLoading(true)
    try {
      await onStateChange(newState)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddNote = async () => {
    if (!noteText.trim()) return
    setIsLoading(true)
    try {
      await onAddNote(noteText)
      setNoteText('')
    } finally {
      setIsLoading(false)
    }
  }

  const statusColors: Record<string, string> = {
    detected: 'bg-gray-100 text-gray-700',
    reviewed: 'bg-blue-100 text-blue-700',
    in_crm: 'bg-green-100 text-green-700',
    discarded: 'bg-purple-100 text-purple-700',
  }

  const urgencyColors: Record<string, string> = {
    high: 'text-red-600',
    medium: 'text-orange-600',
    low: 'text-yellow-600',
  }

  const urgencyLabel = (urgency: string) => {
    switch (urgency) {
      case 'high':
        return '🔴'
      case 'medium':
        return '🟠'
      case 'low':
        return '🟡'
      default:
        return ''
    }
  }

  return (
    <>
      <tr
        onClick={() => setIsExpanded(!isExpanded)}
        className="border-b hover:bg-gray-50 cursor-pointer"
      >
        <td className="px-4 py-3 text-sm font-medium">{opportunity.title}</td>
        <td className="px-4 py-3 text-sm">{opportunity.funder_name}</td>
        <td className="px-4 py-3 text-sm">
          ${(opportunity.amount_max_cop || 0).toLocaleString('es-CO')}
        </td>
        <td className="px-4 py-3 text-sm">
          {opportunity.deadline
            ? new Date(opportunity.deadline).toLocaleDateString('es-CO')
            : 'N/A'}
        </td>
        <td className="px-4 py-3">
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              statusColors[opportunity.status] || 'bg-gray-100'
            }`}
          >
            {opportunity.status}
          </span>
        </td>
        <td className={`px-4 py-3 text-sm font-bold ${urgencyColors[opportunity.urgency]}`}>
          {urgencyLabel(opportunity.urgency)}
        </td>
        <td className="px-4 py-3 text-center">
          <button
            className="text-lg"
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </td>
      </tr>

      {isExpanded && (
        <tr className="bg-gray-50 border-b">
          <td colSpan={7} className="px-4 py-4">
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1">Descripción</p>
                <p className="text-sm text-gray-700">
                  {opportunity.description || 'Sin descripción'}
                </p>
              </div>

              <div className="flex gap-2">
                <select
                  disabled={isLoading}
                  onChange={(e) => handleStateChange(e.target.value)}
                  className="px-2 py-1 border border-gray-300 rounded text-xs"
                >
                  <option value="">Cambiar estado</option>
                  <option value="detected">Detectada</option>
                  <option value="reviewed">Revisada</option>
                  <option value="in_crm">En gestión</option>
                  <option value="discarded">Descartada</option>
                </select>

                <input
                  type="text"
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Agregar nota..."
                  disabled={isLoading}
                  className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs"
                />

                <button
                  onClick={handleAddNote}
                  disabled={isLoading || !noteText.trim()}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isLoading ? '...' : 'Agregar'}
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
