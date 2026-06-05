'use client'

interface FilterSelectProps {
  label: string
  ariaLabel: string
  value: string | undefined
  options: Array<{ value: string; label: string }>
  onChange: (value: string | undefined) => void
  onFocus?: (e: React.FocusEvent<HTMLSelectElement>) => void
  onBlur?: (e: React.FocusEvent<HTMLSelectElement>) => void
}

export function FilterSelect({
  label,
  ariaLabel,
  value,
  options,
  onChange,
  onFocus,
  onBlur,
}: FilterSelectProps) {
  return (
    <select
      aria-label={ariaLabel}
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value || undefined)}
      onFocus={onFocus}
      onBlur={onBlur}
      style={{
        padding: '6px 10px',
        fontSize: '13px',
        border: '1px solid var(--border)',
        borderRadius: '4px',
        backgroundColor: 'var(--bg-subtle)',
        color: 'var(--text)',
        cursor: 'pointer',
        transition: 'box-shadow 0.2s ease',
      }}
    >
      <option value="">{label}</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
