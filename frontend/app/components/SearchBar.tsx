'use client'

import { useState, useTransition } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'

interface Props {
  placeholder?: string
}

export default function SearchBar({ placeholder = 'Buscar por título o descripción...' }: Props) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const [isPending, startTransition] = useTransition()

  function applySearch(newQuery: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (newQuery.trim()) {
      params.set('q', newQuery.trim())
    } else {
      params.delete('q')
    }
    params.delete('page') // Reset paginación al cambiar búsqueda
    startTransition(() => {
      router.push(`${pathname}?${params.toString()}`)
    })
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    applySearch(query)
  }

  function handleClear() {
    setQuery('')
    applySearch('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        background: 'var(--bg3)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r)',
        padding: '6px 12px',
        width: 320,
        flexShrink: 0,
      }}
    >
      <span style={{ color: 'var(--muted)', fontSize: 14 }}>🔍</span>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        style={{
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: 'var(--text)',
          fontFamily: 'var(--sans)',
          fontSize: 12.5,
          width: '100%',
        }}
      />
      {query && (
        <button
          type="button"
          onClick={handleClear}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--muted)',
            cursor: 'pointer',
            fontSize: 14,
            padding: 0,
          }}
          title="Limpiar"
        >
          ✕
        </button>
      )}
      <button
        type="submit"
        disabled={isPending}
        style={{
          background: isPending ? 'var(--bg4)' : 'var(--go-bg)',
          border: '1px solid var(--go-bdr)',
          color: 'var(--go)',
          cursor: isPending ? 'wait' : 'pointer',
          fontSize: 11,
          fontWeight: 600,
          padding: '3px 8px',
          borderRadius: 4,
        }}
      >
        {isPending ? '...' : 'Buscar'}
      </button>
    </form>
  )
}
