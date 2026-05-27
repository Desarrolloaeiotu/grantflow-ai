'use client'

import { useState } from 'react'
import { Opportunity, FilterState } from '../types'
import FilterBar from './shared/FilterBar'
import ExpandableRow from './shared/ExpandableRow'
import { cambiarEstadoOportunidad, agregarNotaOportunidad } from '../actions/nacional-actions'

interface PipelineSectionProps {
  opportunities: Opportunity[]
}

export default function PipelineSection({ opportunities }: PipelineSectionProps) {
  const [filters, setFilters] = useState<FilterState>({
    estado: 'in_crm', // Default: show only in_crm opportunities
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
    // For pipeline: show only in_crm or reviewed statuses
    if (opp.status !== 'in_crm' && opp.status !== 'reviewed') return false

    if (filters.estado && opp.status !== filters.estado) return false
    if (filters.urgencia && opp.urgency !== filters.urgencia) return false
    if (filters.financiador && opp.funder_name !== filters.financiador) return false
    if (filters.sector && opp.capital_type !== filters.sector) return false
    return true
  })

  // Calculate metrics - only for in_crm and reviewed
  const metrics = {
    enGestion: opportunities.filter((o) => o.status === 'in_crm').length,
    revisadas: opportunities.filter((o) => o.status === 'reviewed').length,
    total: opportunities.filter((o) => o.status === 'in_crm' || o.status === 'reviewed').length,
  }

  // Distribution by funder for opportunities in active management
  const activeMgmtOpps = opportunities.filter((o) => o.status === 'in_crm' || o.status === 'reviewed')
  const distributionByFunder = financiadores.map((funder) => ({
    name: funder,
    count: activeMgmtOpps.filter((o) => o.funder_name === funder).length,
  }))
  .filter((item) => item.count > 0)
  .sort((a, b) => b.count - a.count)

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
        <h2>Pipeline en Gestión</h2>
      </div>

      {/* Summary Cards */}
      <div className="kpi-row">
        <div className="kpi go">
          <div className="kpi-label">En gestión (CRM)</div>
          <div className="kpi-val go">{metrics.enGestion}</div>
          <div className="kpi-sub">{((metrics.enGestion / Math.max(metrics.total, 1)) * 100).toFixed(0)}% del pipeline</div>
        </div>
        <div className="kpi warn">
          <div className="kpi-label">Revisadas (pendiente CRM)</div>
          <div className="kpi-val warn">{metrics.revisadas}</div>
          <div className="kpi-sub">{((metrics.revisadas / Math.max(metrics.total, 1)) * 100).toFixed(0)}% del pipeline</div>
        </div>
        <div className="kpi blue">
          <div className="kpi-label">Total en gestión</div>
          <div className="kpi-val blue">{metrics.total}</div>
          <div className="kpi-sub">oportunidades activas</div>
        </div>
      </div>

      {/* Distribution by Funder - Bar Chart */}
      {distributionByFunder.length > 0 && (
        <div style={{ padding: '16px 20px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r)', marginBottom: 24 }}>
          <div className="section-hd" style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 500 }}>Distribución del Pipeline por Financiador</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {distributionByFunder.map((item) => (
              <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ width: 160, fontSize: 12, fontWeight: 500, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.name}
                </div>
                <div style={{ flex: 1, height: 6, background: 'var(--bg3)', borderRadius: 3, overflow: 'hidden' }}>
                  <div
                    style={{ height: '100%', background: 'var(--go)', width: `${(item.count / maxCount) * 100}%` }}
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

      {/* Opportunities Table */}
      <div className="data-table-wrap">
        {filteredOpps.length === 0 ? (
          <div className="empty-state">
            No hay oportunidades en el pipeline que coincidan con los filtros seleccionados
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Título</th>
                <th>Financiador</th>
                <th>Monto COP</th>
                <th>Vencimiento</th>
                <th>Estado</th>
                <th>Urgencia</th>
                <th style={{ width: 32 }}></th>
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
      <div style={{ fontSize: 12, color: 'var(--muted)', padding: '12px 16px', background: 'var(--bg3)', borderRadius: 'var(--r)', border: '1px solid var(--border)', marginTop: 24 }}>
        Mostrando <strong>{filteredOpps.length}</strong> de{' '}
        <strong>{metrics.total}</strong> oportunidades en gestión activa
      </div>
    </div>
  )
}
