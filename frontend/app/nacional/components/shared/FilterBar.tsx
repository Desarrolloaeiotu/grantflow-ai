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
  const selectStyle = {
    padding: '5px 8px',
    border: '1px solid var(--border)',
    borderRadius: 'var(--r)',
    fontSize: 12,
    background: 'var(--bg2)',
    color: 'var(--text)',
    fontFamily: 'var(--sans)',
    cursor: 'pointer',
  }

  return (
    <div style={{ display: 'flex', gap: 12, padding: '12px 16px', background: 'var(--bg3)', borderBottom: '1px solid var(--border)' }}>
      {/* Estado filter */}
      <select
        value={activeFilters.estado}
        onChange={(e) => onFilterChange('estado', e.target.value)}
        style={selectStyle}
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
        style={selectStyle}
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
        style={selectStyle}
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
        style={selectStyle}
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
