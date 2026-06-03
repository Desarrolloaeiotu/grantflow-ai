'use client'

import { useState } from 'react'
import { Opportunity } from '../../types'
import OpportunityEvaluationModal, { EvaluationData } from './OpportunityEvaluationModal'
import { evaluarOportunidad } from '../../actions/opportunities-actions'
import styles from './OpportunityCard.module.css'

interface OpportunityCardProps {
  opportunity: Opportunity
  onStateChange?: (newState: string) => void
}

const CRITERION_NAMES = {
  c1: 'Alineación',
  c2: 'Modelo',
  c3: 'Ticket',
  c4: 'Viabilidad',
  c5: 'Relacional',
}

export default function OpportunityCard({
  opportunity,
  onStateChange,
}: OpportunityCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)

  const scoreTotal = opportunity.score_total || 0
  const daysToDeadline = calculateDaysToDeadline(opportunity.deadline)
  const urgencyClass = getUrgencyClass(daysToDeadline)
  const urgencyLabel = getUrgencyLabel(daysToDeadline)

  const formatCOP = (amount: number | null | undefined) => {
    if (!amount) return null
    if (amount >= 1_000_000_000) {
      return `USD $${(amount / 1_000_000_000).toFixed(1)}B`
    }
    if (amount >= 1_000_000) {
      return `USD $${Math.round(amount / 1_000_000)}M`
    }
    return `USD $${Math.round(amount)}`
  }

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return null
    const date = new Date(dateString)
    return date.toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const handleStateChange = (newState: string) => {
    if (onStateChange) {
      onStateChange(newState)
    }
  }

  const handleEvaluation = async (data: EvaluationData) => {
    const result = await evaluarOportunidad(opportunity.id, data)

    if (!result.success) {
      throw new Error(result.error || 'Error al guardar evaluación')
    }

    if (data.decision === 'accept') {
      handleStateChange('in_crm')
    }
  }

  const amount = formatCOP(opportunity.amount_max_cop || opportunity.amount_min_cop)
  const deadline = formatDate(opportunity.deadline)

  return (
    <>
    <div className={styles.card}>
      {/* COMPACT HEADER */}
      <div className={styles.compactHeader}>
        <div className={styles.titleWrapper}>
          <h3 className={styles.title}>{opportunity.title}</h3>
          <p className={styles.funderName}>{opportunity.funder_name || '—'}</p>
        </div>

        <div className={styles.headerMetrics}>
          <div className={styles.scoreBadge}>
            <span className={styles.scoreValue}>{scoreTotal}</span>
            <span className={styles.scoreMax}>/10</span>
          </div>

          <div className={`${styles.urgencyBadge} ${styles[urgencyClass]}`}>
            <div className={styles.urgencyLabel}>{urgencyLabel}</div>
            <div className={styles.urgencyDays}>{Math.max(0, daysToDeadline)}d</div>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className={styles.mainContent}>
        {/* LEFT COLUMN */}
        <div className={styles.leftColumn}>
          {/* Meta Info */}
          <div className={styles.metaBox}>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>MONTO</span>
              <span className={styles.metaValue}>{amount || '—'}</span>
            </div>
            <div className={styles.metaItem}>
              <span className={styles.metaLabel}>VENCE</span>
              <span className={styles.metaValue}>{deadline || '—'}</span>
            </div>
          </div>

          {/* Funder Info */}
          <div className={styles.contactBox}>
            <h4 className={styles.boxTitle}>FINANCIADOR</h4>
            <div className={styles.contactInfo}>
              <p className={styles.contactItem}>
                <strong>{opportunity.funder_name || '—'}</strong>
              </p>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        {opportunity.score_details && (
          <div className={styles.rightColumn}>
            <div className={styles.scoringBox}>
              <h4 className={styles.boxTitle}>CRITERIOS</h4>
              <div className={styles.scoringGrid}>
                {['c1', 'c2', 'c3', 'c4', 'c5'].map((criterion) => {
                  const value = opportunity.score_details?.[criterion as keyof typeof opportunity.score_details] ?? 0
                  const percentage = ((value as number) / 2) * 100
                  return (
                    <div key={criterion} className={styles.scoringItem}>
                      <div className={styles.criterionLabel}>{criterion}</div>
                      <div className={styles.scoringBar}>
                        <div
                          className={styles.scoringBarFill}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <div className={styles.scoringValue}>{value}/2</div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Window + Decision Badge */}
            {(opportunity.market_window || opportunity.decision) && (
              <div className={styles.badgeBox}>
                {opportunity.market_window && (
                  <span className={styles.windowBadge}>{opportunity.market_window}</span>
                )}
                {opportunity.decision === 'go' && (
                  <span className={styles.goBadge}>✓ GO</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ACTION BUTTONS */}
      <div className={styles.actions}>
        {opportunity.url_rfp && (
          <a
            href={opportunity.url_rfp}
            target="_blank"
            rel="noopener noreferrer"
            className={`${styles.actionButton} ${styles.view}`}
          >
            📄 Ver
          </a>
        )}
        <button
          className={`${styles.actionButton} ${styles.primary}`}
          onClick={() => setIsModalOpen(true)}
        >
          ⭐ Evaluar
        </button>
      </div>
    </div>

    {/* Evaluation Modal */}
    <OpportunityEvaluationModal
      opportunityId={opportunity.id}
      opportunityTitle={opportunity.title}
      isOpen={isModalOpen}
      onClose={() => setIsModalOpen(false)}
      onSubmit={handleEvaluation}
    />
    </>
  )
}

function calculateDaysToDeadline(deadline: string | null | undefined): number {
  if (!deadline) return Infinity
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const deadlineDate = new Date(deadline)
  deadlineDate.setHours(0, 0, 0, 0)
  const diff = deadlineDate.getTime() - today.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function getUrgencyLabel(days: number): string {
  if (days <= 7) return 'CRÍTICO'
  if (days <= 15) return 'ALTO'
  if (days <= 30) return 'MEDIO'
  return 'BAJO'
}

function getUrgencyClass(days: number): string {
  if (days <= 7) return 'urgencyHigh'
  if (days <= 15) return 'urgencyMedium'
  return 'urgencyLow'
}
