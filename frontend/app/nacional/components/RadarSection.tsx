'use client'

import { useState } from 'react'
import { Opportunity, FilterState } from '../types'
import FilterBar from './shared/FilterBar'
import OpportunityCard from './shared/OpportunityCard'
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
    <div className="page">
      <div className="section-hd">
        <h2>Radar Nacional</h2>
      </div>

      {/* Metric Cards */}
      <div className="kpi-row">
        <div className="kpi">
          <div className="kpi-label">Detectadas</div>
          <div className="kpi-val">{metrics.detectadas}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Revisadas</div>
          <div className="kpi-val">{metrics.revisadas}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">En gestión</div>
          <div className="kpi-val">{metrics.enGestion}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Cerradas</div>
          <div className="kpi-val">{metrics.cerradas}</div>
        </div>
      </div>

      {/* Distribution by Funder Bar Chart */}
      {distributionByFunder.length > 0 && (
        <div style={{ padding: '16px 20px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r)', marginBottom: 24 }}>
          <div className="section-hd" style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 500 }}>Distribución por Financiador</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {distributionByFunder.map((item) => (
              <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ width: 128, fontSize: 12, fontWeight: 500, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.name}
                </div>
                <div style={{ flex: 1, height: 6, background: 'var(--bg3)', borderRadius: 3, overflow: 'hidden' }}>
                  <div
                    style={{ height: '100%', background: 'var(--blue)', width: `${(item.count / maxCount) * 100}%` }}
                  />
                </div>
                <div style={{ width: 48, textAlign: 'right', fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>
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

      {/* Opportunities Grid */}
      {filteredOpps.length === 0 ? (
        <div className="empty-state">
          No hay oportunidades que coincidan con los filtros seleccionados
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(520px, 1fr))',
            gap: '20px',
            marginBottom: '24px',
          }}
        >
          {filteredOpps.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              onStateChange={(newState) => handleStateChange(opp.id, newState)}
              onAddNote={(note) => handleAddNote(opp.id, note)}
            />
          ))}
        </div>
      )}

      {/* Summary */}
      <div style={{ fontSize: 12, color: 'var(--muted)', padding: '12px 16px', background: 'var(--bg3)', borderRadius: 'var(--r)', border: '1px solid var(--border)', marginTop: 24 }}>
        Mostrando <strong>{filteredOpps.length}</strong> de{' '}
        <strong>{opportunities.length}</strong> oportunidades
      </div>
    </div>
  )
}
