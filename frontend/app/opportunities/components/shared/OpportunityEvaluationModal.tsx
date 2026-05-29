'use client'

import { useState } from 'react'
import styles from './OpportunityEvaluationModal.module.css'

interface OpportunityEvaluationModalProps {
  opportunityId: string
  opportunityTitle: string
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: EvaluationData) => Promise<void>
}

export interface EvaluationData {
  decision: 'accept' | 'reject'
  reason?: string
  observations: string
}

const REJECTION_REASONS = [
  'Sin presupuesto',
  'Fuera de scope',
  'Capacidad insuficiente',
  'Conflicto de timing',
  'Información incompleta',
  'Otra',
]

export default function OpportunityEvaluationModal({
  opportunityId,
  opportunityTitle,
  isOpen,
  onClose,
  onSubmit,
}: OpportunityEvaluationModalProps) {
  const [decision, setDecision] = useState<'accept' | 'reject' | null>(null)
  const [reason, setReason] = useState('')
  const [observations, setObservations] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  if (!isOpen) return null

  const handleSubmit = async () => {
    if (!decision) {
      setError('Selecciona una decisión')
      return
    }

    if (decision === 'reject' && !reason) {
      setError('Selecciona una razón para denegar')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      await onSubmit({
        decision,
        reason: decision === 'reject' ? reason : undefined,
        observations,
      })
      resetForm()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar')
    } finally {
      setIsLoading(false)
    }
  }

  const resetForm = () => {
    setDecision(null)
    setReason('')
    setObservations('')
    setError('')
  }

  const handleCancel = () => {
    resetForm()
    onClose()
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className={styles.backdrop}
        onClick={handleCancel}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className={styles.modal} role="dialog" aria-labelledby="modal-title">
        {/* Header */}
        <div className={styles.header}>
          <h2 id="modal-title" className={styles.title}>
            Evaluar oportunidad
          </h2>
          <button
            className={styles.closeButton}
            onClick={handleCancel}
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className={styles.body}>
          {/* Opportunity Title */}
          <div className={styles.oppTitle}>
            <p>{opportunityTitle}</p>
          </div>

          {/* Decision Section */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>¿Qué decisión tomas?</label>
            <div className={styles.decisionButtons}>
              <button
                className={`${styles.decisionButton} ${styles.accept} ${
                  decision === 'accept' ? styles.selected : ''
                }`}
                onClick={() => {
                  setDecision('accept')
                  setReason('')
                  setError('')
                }}
              >
                <span className={styles.icon}>✓</span>
                <span>ACEPTAR</span>
              </button>

              <button
                className={`${styles.decisionButton} ${styles.reject} ${
                  decision === 'reject' ? styles.selected : ''
                }`}
                onClick={() => {
                  setDecision('reject')
                  setError('')
                }}
              >
                <span className={styles.icon}>✕</span>
                <span>DENEGAR</span>
              </button>
            </div>
          </div>

          {/* Rejection Reason - only if reject selected */}
          {decision === 'reject' && (
            <div className={styles.section}>
              <label htmlFor="reason-select" className={styles.sectionLabel}>
                Razón de rechazo
              </label>
              <select
                id="reason-select"
                className={styles.select}
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value)
                  setError('')
                }}
              >
                <option value="">Selecciona una razón...</option>
                {REJECTION_REASONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Observations */}
          <div className={styles.section}>
            <label htmlFor="observations" className={styles.sectionLabel}>
              Observaciones
            </label>
            <textarea
              id="observations"
              className={styles.textarea}
              placeholder="Agrega observaciones (opcional)"
              value={observations}
              onChange={(e) => setObservations(e.target.value)}
              rows={4}
            />
          </div>

          {/* Error Message */}
          {error && <div className={styles.error}>{error}</div>}
        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <button
            className={`${styles.button} ${styles.secondary}`}
            onClick={handleCancel}
            disabled={isLoading}
          >
            Cancelar
          </button>
          <button
            className={`${styles.button} ${styles.primary}`}
            onClick={handleSubmit}
            disabled={!decision || isLoading}
          >
            {isLoading ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </>
  )
}
