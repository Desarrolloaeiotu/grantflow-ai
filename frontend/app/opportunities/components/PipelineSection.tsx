'use client'

import { useState } from 'react'
import { Opportunity } from '../types'
import { cambiarEstadoOportunidad, agregarNotaOportunidad } from '../actions/opportunities-actions'

interface PipelineSectionProps {
  opportunities: Opportunity[]
}

const WINDOW_LABEL: Record<string, string> = {
  funding_colombia: 'Colombia',
  funding_global:   'Global',
  strategic:        'Estratégico',
  latam:            'LATAM',
}

function formatAmount(opp: Opportunity): string {
  const v = opp.amount_max_cop ?? opp.amount_min_cop
  if (!v) return '—'
  if (v >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`
  if (v >= 1_000_000) return `$${Math.round(v / 1_000_000)}M`
  return `$${v.toLocaleString()}`
}

function formatPipelineValue(v: number): string {
  if (v >= 1_000_000_000) return `COP $${(v / 1_000_000_000).toFixed(1)}B`
  if (v >= 1_000_000) return `COP $${Math.round(v / 1_000_000)}M`
  return `COP $${v.toLocaleString()}`
}

type DecisionFilter = 'all' | 'go' | 'pending'

export default function PipelineSection({ opportunities }: PipelineSectionProps) {
  const [filter, setFilter] = useState<DecisionFilter>('go')

  const pipeline = opportunities.filter(o => o.decision === 'go' || o.decision === 'pending')
  const go       = opportunities.filter(o => o.decision === 'go')
  const pending  = opportunities.filter(o => o.decision === 'pending')

  const totalValue = go.reduce((sum, o) => sum + (o.amount_max_cop ?? o.amount_min_cop ?? 0), 0)

  const filtered = filter === 'all' ? pipeline : pipeline.filter(o => o.decision === filter)

  return (
    <div className="page">
      {/* KPIs */}
      <div className="kpi-row">
        <div className="kpi go">
          <div className="kpi-label">GO</div>
          <div className="kpi-val go">{go.length}</div>
          <div className="kpi-sub">en gestión</div>
        </div>
        <div className="kpi warn">
          <div className="kpi-label">Pendientes</div>
          <div className="kpi-val warn">{pending.length}</div>
          <div className="kpi-sub">por revisar</div>
        </div>
        <div className="kpi blue">
          <div className="kpi-label">Total activas</div>
          <div className="kpi-val blue">{pipeline.length}</div>
          <div className="kpi-sub">en pipeline</div>
        </div>
        <div className="kpi violet">
          <div className="kpi-label">Valor pipeline</div>
          <div className="kpi-val violet" style={{ fontSize: 15 }}>
            {formatPipelineValue(totalValue)}
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="filters">
        <button className={`filter-btn${filter === 'all' ? ' on' : ''}`} onClick={() => setFilter('all')}>
          Todos ({pipeline.length})
        </button>
        <button className={`filter-btn${filter === 'go' ? ' on' : ''}`} onClick={() => setFilter('go')}>
          GO ({go.length})
        </button>
        <button className={`filter-btn${filter === 'pending' ? ' on' : ''}`} onClick={() => setFilter('pending')}>
          Pendientes ({pending.length})
        </button>
      </div>

      {/* Tabla */}
      {filtered.length === 0 ? (
        <div className="empty-state">
          <strong>Sin oportunidades en pipeline.</strong><br />
          Las oportunidades GO y pendientes de revisión aparecerán aquí.
        </div>
      ) : (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Título</th>
                <th>Fuente</th>
                <th>Monto</th>
                <th>Vencimiento</th>
                <th>Decisión</th>
                <th>Ventana</th>
                <th style={{ width: 32 }}></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(opp => (
                <PipelineRow key={opp.id} opp={opp} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function PipelineRow({ opp }: { opp: Opportunity }) {
  const [expanded, setExpanded] = useState(false)
  const [note,     setNote]     = useState('')
  const [saving,   setSaving]   = useState(false)

  const handleStatus = async (v: string) => {
    if (!v) return
    setSaving(true)
    await cambiarEstadoOportunidad(opp.id, v as 'detected' | 'reviewed' | 'in_crm' | 'cerrada')
    setSaving(false)
  }

  const handleNote = async () => {
    if (!note.trim()) return
    setSaving(true)
    await agregarNotaOportunidad(opp.id, note)
    setSaving(false)
    setNote('')
  }

  const deadline = opp.deadline
    ? new Date(opp.deadline).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: '2-digit' })
    : '—'

  return (
    <>
      <tr style={{ cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
        <td style={{ maxWidth: 280 }}>
          <div style={{ fontWeight: 500, fontSize: 12.5, color: 'var(--text)', lineHeight: 1.4 }}>
            {opp.title.length > 80 ? opp.title.slice(0, 80) + '…' : opp.title}
          </div>
        </td>
        <td className="td-muted">{opp.source_name ?? '—'}</td>
        <td className="td-go td-mono">{formatAmount(opp)}</td>
        <td className="td-muted td-mono" style={{ fontSize: 11 }}>{deadline}</td>
        <td>
          <span className={`chip ${opp.decision === 'go' ? 'chip-go' : 'chip-warn'}`}>
            {opp.decision === 'go' ? 'GO' : 'PENDIENTE'}
          </span>
        </td>
        <td className="td-muted" style={{ fontSize: 11 }}>
          {opp.market_window ? (WINDOW_LABEL[opp.market_window] ?? opp.market_window) : '—'}
        </td>
        <td style={{ textAlign: 'center', color: 'var(--muted2)' }}>
          {expanded ? '▼' : '▶'}
        </td>
      </tr>

      {expanded && (
        <tr style={{ background: 'var(--bg3)' }}>
          <td colSpan={7} style={{ padding: '14px 16px' }}>
            {opp.description && (
              <p style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12, lineHeight: 1.55 }}>
                {opp.description.length > 300
                  ? opp.description.slice(0, 300) + '…'
                  : opp.description}
              </p>
            )}
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <select
                disabled={saving}
                defaultValue=""
                onChange={e => handleStatus(e.target.value)}
                style={{
                  padding: '5px 8px',
                  border: '1px solid var(--border)',
                  borderRadius: 6,
                  fontSize: 12,
                  background: 'var(--bg2)',
                  color: 'var(--text)',
                }}
              >
                <option value="" disabled>Cambiar estado</option>
                <option value="detected">Detectada</option>
                <option value="reviewed">Revisada</option>
                <option value="in_crm">En gestión (CRM)</option>
                <option value="cerrada">Cerrada</option>
              </select>
              <input
                type="text"
                value={note}
                onChange={e => setNote(e.target.value)}
                placeholder="Agregar nota..."
                disabled={saving}
                style={{
                  flex: 1,
                  padding: '5px 8px',
                  border: '1px solid var(--border)',
                  borderRadius: 6,
                  fontSize: 12,
                  background: 'var(--bg2)',
                  minWidth: 160,
                }}
              />
              <button
                onClick={handleNote}
                disabled={saving || !note.trim()}
                className="link-btn primary"
              >
                {saving ? '...' : 'Guardar nota'}
              </button>
              {opp.url_rfp && (
                <a
                  href={opp.url_rfp}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-btn"
                  onClick={e => e.stopPropagation()}
                >
                  ↗ Ver convocatoria
                </a>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
