'use client'

import { useState } from 'react'
import { Opportunity, FilterState } from '../types'
import FilterBar from './shared/FilterBar'
import ExpandableRow from './shared/ExpandableRow'
import { cambiarEstadoOportunidad, agregarNotaOportunidad } from '../actions/nacional-actions'

interface RadarSectionProps {
  opportunities: Opportunity[]
}

export default function RadarSection({ opportunities }: RadarSectionProps) {
  const [filters, setFilters] = useState<FilterState>({
    estado: '',
    urgencia: '',
    financiador: '',
    sector: '',
  })

  // Extract unique financiadores y sectores
  const financiadores = Array.from(
    new Set(opportunities.map((o) => o.funder_name).filter(Boolean))
  ).sort()

  const sectores = Array.from(
    new Set(opportunities.flatMap((o) => (o.capital_type ? [o.capital_type] : [])))
  ).sort()

  // Apply filters
  const filteredOpps = opportunities.filter((opp) => {
    if (filters.estado && opp.status !== filters.estado) return false
    if (filters.urgencia && opp.urgency !== filters.urgencia) return false
    if (filters.financiador && opp.funder_name !== filters.financiador) return false
    if (filters.sector && opp.capital_type !== filters.sector) return false
    return true
  })

  // Calculate metrics
  const metrics = {
    detectadas: opportunities.filter((o) => o.status === 'detected').length,
    revisadas: opportunities.filter((o) => o.status === 'reviewed').length,
    enGestion: opportunities.filter((o) => o.status === 'in_crm').length,
    cerradas: opportunities.filter((o) => o.status === 'discarded').length,
  }

  // Distribution by funder for bar chart
  const distributionByFunder = financiadores.map((funder) => ({
    name: funder,
    count: opportunities.filter((o) => o.funder_name === funder).length,
  }))

  // Handler functions
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const handleStateChange = async (opportunityId: string, newState: string) => {
    const result = await cambiarEstadoOportunidad(
      opportunityId,
      newState as 'detected' | 'reviewed' | 'in_crm' | 'cerrada'
    )
    if (!result.success) {
      console.error('Error changing state:', result.error)
      alert(`Error: ${result.error}`)
    }
  }

  const handleAddNote = async (opportunityId: string, note: string) => {
    const result = await agregarNotaOportunidad(opportunityId, note)
    if (!result.success) {
      console.error('Error adding note:', result.error)
      alert(`Error: ${result.error}`)
    }
  }

  // Maximum count for bar chart scaling
  const maxCount = Math.max(...distributionByFunder.map((d) => d.count), 1)

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Radar Nacional</h1>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-gray-600 text-sm font-medium mb-2">Detectadas</p>
          <p className="text-3xl font-bold text-gray-900">{metrics.detectadas}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-gray-600 text-sm font-medium mb-2">Revisadas</p>
          <p className="text-3xl font-bold text-gray-900">{metrics.revisadas}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-gray-600 text-sm font-medium mb-2">En gestión</p>
          <p className="text-3xl font-bold text-gray-900">{metrics.enGestion}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <p className="text-gray-600 text-sm font-medium mb-2">Cerradas</p>
          <p className="text-3xl font-bold text-gray-900">{metrics.cerradas}</p>
        </div>
      </div>

      {/* Distribution by Funder Bar Chart */}
      {distributionByFunder.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Distribución por Financiador
          </h2>
          <div className="space-y-3">
            {distributionByFunder.map((item) => (
              <div key={item.name} className="flex items-center gap-4">
                <div className="w-32 text-sm font-medium text-gray-700 truncate">
                  {item.name}
                </div>
                <div className="flex-1 h-6 bg-gray-100 rounded overflow-hidden">
                  <div
                    className="h-full bg-blue-500"
                    style={{ width: `${(item.count / maxCount) * 100}%` }}
                  />
                </div>
                <div className="w-12 text-right text-sm font-semibold text-gray-900">
                  {item.count}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <FilterBar
        activeFilters={filters}
        onFilterChange={handleFilterChange}
        financiadores={financiadores}
        sectores={sectores}
      />

      {/* Opportunities Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
        {filteredOpps.length === 0 ? (
          <div className="p-8 text-center text-gray-600">
            No hay oportunidades que coincidan con los filtros seleccionados
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Título
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Financiador
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Monto COP
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Vencimiento
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Estado
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                  Urgencia
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">
                  Expandir
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredOpps.map((opp) => (
                <ExpandableRow
                  key={opp.id}
                  opportunity={opp}
                  onStateChange={(newState) => handleStateChange(opp.id, newState)}
                  onAddNote={(note) => handleAddNote(opp.id, note)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Summary */}
      <div className="text-sm text-gray-600 p-4 bg-gray-50 rounded-lg border border-gray-200">
        Mostrando <strong>{filteredOpps.length}</strong> de{' '}
        <strong>{opportunities.length}</strong> oportunidades
      </div>
    </div>
  )
}
