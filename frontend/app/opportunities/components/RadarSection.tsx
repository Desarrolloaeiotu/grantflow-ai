'use client'

import { useState } from 'react'
import { OpportunityList } from '../types'
import OpportunityCard from './shared/OpportunityCard'
import { cambiarEstadoOportunidad } from '../actions/opportunities-actions'

interface RadarSectionProps {
  initialList: OpportunityList | null
}

const WINDOW_LABEL: Record<string, string> = {
  funding_colombia: 'Funding Colombia',
  funding_global: 'Funding Global',
  strategic: 'Estratégico',
  latam: 'LATAM',
}

export default function RadarSection({ initialList }: RadarSectionProps) {
  const [filters, setFilters] = useState({
    decision: '',
    urgency: '',
    window: '',
  })

  if (!initialList || initialList.items.length === 0) {
    return (
      <div className="page">
        <div className="empty-state">
          <strong>Sin oportunidades.</strong>
          <br />
          Corre el scraper para detectar nuevas oportunidades.
        </div>
      </div>
    )
  }

  const opportunities = initialList.items
  const metrics = {
    detectadas: opportunities.length,
    go: opportunities.filter(o => o.decision === 'go').length,
    pendientes: opportunities.filter(o => o.decision === 'pending').length,
    nogo: opportunities.filter(o => o.decision === 'no_go').length,
  }

  const filteredOpps = opportunities.filter((opp) => {
    if (filters.decision && opp.decision !== filters.decision) return false
    if (filters.urgency && opp.urgency !== filters.urgency) return false
    if (filters.window && opp.market_window !== filters.window) return false
    return true
  })

  const handleFilterChange = (key: 'decision' | 'urgency' | 'window', value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === prev[key] ? '' : value,
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

  return (
    <div className="page">
      <div className="section-hd">
        <h2>Radar Global</h2>
      </div>

      {/* Metric Cards */}
      <div className="kpi-row">
        <div className="kpi">
          <div className="kpi-label">Detectadas</div>
          <div className="kpi-val">{metrics.detectadas}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">GO</div>
          <div className="kpi-val" style={{ color: 'var(--go)' }}>{metrics.go}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Pendientes</div>
          <div className="kpi-val" style={{ color: 'var(--warn)' }}>{metrics.pendientes}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">No-Go</div>
          <div className="kpi-val" style={{ color: 'var(--red)' }}>{metrics.nogo}</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '24px', padding: '12px 16px', background: 'var(--bg2)', borderRadius: 'var(--r)', border: '1px solid var(--border)' }}>
        {/* Decision Filters */}
        {['go', 'pending', 'no_go'].map(d => (
          <button
            key={d}
            onClick={() => handleFilterChange('decision', d)}
            style={{
              padding: '6px 12px',
              background: filters.decision === d ? 'var(--accent)' : 'white',
              color: filters.decision === d ? 'white' : 'var(--text)',
              border: `1px solid ${filters.decision === d ? 'var(--accent)' : 'var(--border)'}`,
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {d === 'go' ? 'GO' : d === 'pending' ? 'Pendiente' : 'No-Go'}
          </button>
        ))}

        <span style={{ color: 'var(--border)', margin: '0 4px' }}>|</span>

        {/* Urgency Filters */}
        {(['high', 'medium', 'low'] as const).map(u => (
          <button
            key={u}
            onClick={() => handleFilterChange('urgency', u)}
            style={{
              padding: '6px 12px',
              background: filters.urgency === u ? 'var(--accent)' : 'white',
              color: filters.urgency === u ? 'white' : 'var(--text)',
              border: `1px solid ${filters.urgency === u ? 'var(--accent)' : 'var(--border)'}`,
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {u === 'high' ? '🔴 Alta' : u === 'medium' ? '🟠 Media' : '🟡 Baja'}
          </button>
        ))}

        <span style={{ color: 'var(--border)', margin: '0 4px' }}>|</span>

        {/* Window Filters */}
        {(['funding_global', 'strategic', 'latam'] as const).map(w => (
          <button
            key={w}
            onClick={() => handleFilterChange('window', w)}
            style={{
              padding: '6px 12px',
              background: filters.window === w ? 'var(--accent)' : 'white',
              color: filters.window === w ? 'white' : 'var(--text)',
              border: `1px solid ${filters.window === w ? 'var(--accent)' : 'var(--border)'}`,
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {WINDOW_LABEL[w] || w}
          </button>
        ))}
      </div>

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
            />
          ))}
        </div>
      )}

      {/* Summary */}
      <div style={{ fontSize: '12px', color: 'var(--muted)', padding: '12px 16px', background: 'var(--bg3)', borderRadius: 'var(--r)', border: '1px solid var(--border)', marginTop: '24px' }}>
        Mostrando <strong>{filteredOpps.length}</strong> de <strong>{opportunities.length}</strong> oportunidades
      </div>
    </div>
  )
}
