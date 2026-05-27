'use client'

import { FilterState } from '../../types'

interface FilterBarProps {
  activeFilters: FilterState
  onFilterChange: (key: keyof FilterState, value: string) => void
  financiadores: string[]
  sectores: string[]
}

export default function FilterBar({
  activeFilters,
  onFilterChange,
  financiadores,
  sectores,
}: FilterBarProps) {
  return (
    <div className="flex gap-4 p-4 bg-white border-b border-gray-200">
      {/* Estado filter */}
      <select
        value={activeFilters.estado}
        onChange={(e) => onFilterChange('estado', e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded text-sm"
      >
        <option value="">Todos los estados</option>
        <option value="detected">Detectada</option>
        <option value="reviewed">Revisada</option>
        <option value="in_crm">En gestión</option>
        <option value="discarded">Descartada</option>
      </select>

      {/* Urgencia filter */}
      <select
        value={activeFilters.urgencia}
        onChange={(e) => onFilterChange('urgencia', e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded text-sm"
      >
        <option value="">Todas las urgencias</option>
        <option value="high">7 días</option>
        <option value="medium">15 días</option>
        <option value="low">30 días</option>
      </select>

      {/* Financiador filter */}
      <select
        value={activeFilters.financiador}
        onChange={(e) => onFilterChange('financiador', e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded text-sm"
      >
        <option value="">Todos los financiadores</option>
        {financiadores.map((f) => (
          <option key={f} value={f}>
            {f}
          </option>
        ))}
      </select>

      {/* Sector filter */}
      <select
        value={activeFilters.sector}
        onChange={(e) => onFilterChange('sector', e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded text-sm"
      >
        <option value="">Todos los sectores</option>
        {sectores.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
    </div>
  )
}
