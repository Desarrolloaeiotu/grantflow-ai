# Nacional Colombia: 4-Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a functional Nacional Colombia page where the Alianzas team monitors, analyzes, and manages national funding opportunities detected by the nacional_colombia scraper.

**Architecture:** Server Components fetch fresh data from FastAPI → Supabase. User interactions (state changes, notes) trigger Server Actions that update the backend and invalidate Next.js cache automatically. Four sections (Alertas, Radar, Pipeline, Contactos) share a sidebar navigation and operate independently on the same data source.

**Tech Stack:** Next.js 15 (Server Components + Server Actions), FastAPI (backend), Supabase (PostgreSQL), Tailwind CSS, TypeScript

---

## File Structure Map

```
frontend/app/nacional/
├── page.tsx                         # Main page (renders sidebar + section)
├── layout.tsx                       # Layout (metadata, root styles)
├── components/
│   ├── NacionalSidebar.tsx         # Sidebar navigation (4 sections + badges)
│   ├── AlertasSection.tsx          # Vencimientos + cambios recientes
│   ├── RadarSection.tsx            # Overview + gráfico + tabla filtrada
│   ├── PipelineSection.tsx         # Tabla con expandibles + filtros
│   ├── ContactosSection.tsx        # Tarjetas por financiador + tabla
│   └── shared/
│       ├── FilterBar.tsx           # Reusable filter component
│       ├── ExpandableRow.tsx       # Expandible row for details
│       ├── OpportunityCard.tsx     # Card for oportunidades
│       └── LoadingState.tsx        # Skeletons durante carga
├── actions/
│   └── nacional-actions.ts         # Server Actions (PATCH, POST)
└── data/
    └── nacional-queries.ts         # Fetch functions (GET)
```

---

## Task 1: Setup inicial — Tipos TypeScript

**Files:**
- Create: `frontend/app/nacional/types.ts`

**Goal:** Define TypeScript interfaces for opportunities, contacts, filters, and alerts.

- [ ] **Step 1: Create types.ts with opportunity interface**

```typescript
// frontend/app/nacional/types.ts

export interface Opportunity {
  id: string
  title: string
  description: string | null
  funder_id: string
  funder_name: string
  amount_min_cop: number | null
  amount_max_cop: number | null
  deadline: string | null
  url_rfp: string | null
  source_name: string
  market_window: string
  capital_type: string
  score_total: number
  decision: 'go' | 'no_go' | 'pending'
  urgency: 'high' | 'medium' | 'low'
  status: 'detected' | 'reviewed' | 'in_crm' | 'discarded'
  detected_at: string
  updated_at: string
}

export interface Contact {
  id: string
  full_name: string
  title: string
  email: string
  email_verified: boolean
  linkedin_url: string | null
  funder_id: string
  funder_name: string
  source: 'apollo' | 'manual' | 'linkedin'
  fetched_at: string
}

export interface Alert {
  type: 'vencimiento' | 'cambio'
  opportunityId: string
  title: string
  urgency: 'high' | 'medium' | 'low'
  message: string
  timestamp: string
}

export interface FilterState {
  estado: 'detected' | 'reviewed' | 'in_crm' | 'cerrada' | ''
  urgencia: 'high' | 'medium' | 'low' | ''
  financiador: string // empty or funder_id
  sector: string // empty or sector name
}

export interface DashboardMetrics {
  detected: number
  reviewed: number
  in_crm: number
  cerrada: number
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/types.ts
git commit -m "feat(nacional): add TypeScript types for opportunities, contacts, alerts"
```

---

## Task 2: Data queries — Fetch functions

**Files:**
- Create: `frontend/app/nacional/data/nacional-queries.ts`

**Goal:** Create reusable fetch functions that call the FastAPI backend.

- [ ] **Step 1: Create nacional-queries.ts**

```typescript
// frontend/app/nacional/data/nacional-queries.ts

import { Opportunity, Contact, Alert, DashboardMetrics } from '../types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Fetch all national opportunities (filtered by market_window=funding_colombia)
export async function getOportunidadesNacionales(
  filters?: {
    estado?: string
    urgencia?: string
    financiador?: string
    sector?: string
  }
): Promise<Opportunity[]> {
  const params = new URLSearchParams()
  params.append('window', 'funding_colombia')
  
  if (filters?.estado) params.append('status', filters.estado)
  if (filters?.urgencia) params.append('urgency', filters.urgencia)
  // Note: financiador and sector filtering happens on frontend for now
  
  const res = await fetch(`${API_URL}/api/v1/opportunities?${params.toString()}`, {
    cache: 'no-store', // Always fresh data for Server Components
  })
  
  if (!res.ok) throw new Error('Failed to fetch opportunities')
  const data = await res.json()
  return data.items || []
}

// Fetch dashboard metrics for national opportunities
export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_URL}/api/v1/dashboard/metrics?region=colombia`, {
    cache: 'no-store',
  })
  
  if (!res.ok) throw new Error('Failed to fetch metrics')
  return res.json()
}

// Fetch contacts for national funders
export async function getContactosNacionales(): Promise<Contact[]> {
  const res = await fetch(`${API_URL}/api/v1/contacts?region=colombia`, {
    cache: 'no-store',
  })
  
  if (!res.ok) throw new Error('Failed to fetch contacts')
  const data = await res.json()
  return data.contacts || []
}

// Fetch a single opportunity by ID
export async function getOportunidad(id: string): Promise<Opportunity> {
  const res = await fetch(`${API_URL}/api/v1/opportunities/${id}`, {
    cache: 'no-store',
  })
  
  if (!res.ok) throw new Error(`Failed to fetch opportunity ${id}`)
  return res.json()
}

// Helper: calculate alerts from opportunities
export function generateAlerts(opportunities: Opportunity[]): Alert[] {
  const alerts: Alert[] = []
  const now = new Date()
  
  opportunities.forEach((opp) => {
    if (!opp.deadline) return
    
    const daysUntil = Math.ceil(
      (new Date(opp.deadline).getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    )
    
    if (daysUntil <= 30 && daysUntil > 0) {
      alerts.push({
        type: 'vencimiento',
        opportunityId: opp.id,
        title: opp.title,
        urgency: daysUntil <= 7 ? 'high' : daysUntil <= 15 ? 'medium' : 'low',
        message: `Vence en ${daysUntil} días`,
        timestamp: now.toISOString(),
      })
    }
  })
  
  return alerts.sort((a, b) => 
    a.urgency === 'high' ? -1 : b.urgency === 'high' ? 1 : 0
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/data/nacional-queries.ts
git commit -m "feat(nacional): add data fetch functions for opportunities, contacts, metrics"
```

---

## Task 3: Server Actions — State mutations

**Files:**
- Create: `frontend/app/nacional/actions/nacional-actions.ts`

**Goal:** Implement Server Actions that update opportunity and contact state.

- [ ] **Step 1: Create nacional-actions.ts**

```typescript
// frontend/app/nacional/actions/nacional-actions.ts

'use server'

import { revalidatePath } from 'next/cache'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ActionResult {
  success: boolean
  error?: string
}

// Change opportunity status
export async function cambiarEstadoOportunidad(
  opportunityId: string,
  nuevoEstado: 'detected' | 'reviewed' | 'in_crm' | 'cerrada'
): Promise<ActionResult> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/opportunities/${opportunityId}/status`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nuevoEstado }),
      }
    )
    
    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` }
    }
    
    revalidatePath('/nacional')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// Add note to opportunity
export async function agregarNotaOportunidad(
  opportunityId: string,
  nota: string
): Promise<ActionResult> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/opportunities/${opportunityId}/notes`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: nota,
          created_at: new Date().toISOString(),
        }),
      }
    )
    
    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` }
    }
    
    revalidatePath('/nacional')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// Mark opportunity as priority
export async function marcarPrioridad(
  opportunityId: string,
  isPriority: boolean
): Promise<ActionResult> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/opportunities/${opportunityId}/priority`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_priority: isPriority }),
      }
    )
    
    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` }
    }
    
    revalidatePath('/nacional')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// Mark contact as contacted
export async function marcarContactado(
  contactId: string,
  tipoInteraccion: 'llamada' | 'email' | 'reunion',
  nota?: string
): Promise<ActionResult> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/contacts/${contactId}/interaction`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: tipoInteraccion,
          note: nota || '',
          timestamp: new Date().toISOString(),
        }),
      }
    )
    
    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` }
    }
    
    revalidatePath('/nacional')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/actions/nacional-actions.ts
git commit -m "feat(nacional): add Server Actions for state mutations (status, notes, priority, interactions)"
```

---

## Task 4: Shared components — FilterBar, ExpandableRow, etc.

**Files:**
- Create: `frontend/app/nacional/components/shared/FilterBar.tsx`
- Create: `frontend/app/nacional/components/shared/ExpandableRow.tsx`
- Create: `frontend/app/nacional/components/shared/OpportunityCard.tsx`
- Create: `frontend/app/nacional/components/shared/LoadingState.tsx`

**Goal:** Build reusable UI components used across sections.

- [ ] **Step 1: Create FilterBar.tsx**

```typescript
// frontend/app/nacional/components/shared/FilterBar.tsx

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
        <option value="cerrada">Cerrada</option>
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
```

- [ ] **Step 2: Create ExpandableRow.tsx**

```typescript
// frontend/app/nacional/components/shared/ExpandableRow.tsx

'use client'

import { useState } from 'react'
import { Opportunity } from '../../types'

interface ExpandableRowProps {
  opportunity: Opportunity
  onStateChange: (newState: string) => Promise<void>
  onAddNote: (note: string) => Promise<void>
}

export default function ExpandableRow({
  opportunity,
  onStateChange,
  onAddNote,
}: ExpandableRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [noteText, setNoteText] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleStateChange = async (newState: string) => {
    setIsLoading(true)
    try {
      await onStateChange(newState)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddNote = async () => {
    if (!noteText.trim()) return
    setIsLoading(true)
    try {
      await onAddNote(noteText)
      setNoteText('')
    } finally {
      setIsLoading(false)
    }
  }

  const statusColors = {
    detected: 'bg-gray-100 text-gray-700',
    reviewed: 'bg-blue-100 text-blue-700',
    in_crm: 'bg-green-100 text-green-700',
    cerrada: 'bg-purple-100 text-purple-700',
  }

  const urgencyColors = {
    high: 'text-red-600',
    medium: 'text-orange-600',
    low: 'text-yellow-600',
  }

  return (
    <>
      <tr
        onClick={() => setIsExpanded(!isExpanded)}
        className="border-b hover:bg-gray-50 cursor-pointer"
      >
        <td className="px-4 py-3 text-sm font-medium">{opportunity.title}</td>
        <td className="px-4 py-3 text-sm">{opportunity.funder_name}</td>
        <td className="px-4 py-3 text-sm">
          ${(opportunity.amount_max_cop || 0).toLocaleString('es-CO')}
        </td>
        <td className="px-4 py-3 text-sm">
          {opportunity.deadline
            ? new Date(opportunity.deadline).toLocaleDateString('es-CO')
            : 'N/A'}
        </td>
        <td className="px-4 py-3">
          <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[opportunity.status as keyof typeof statusColors]}`}>
            {opportunity.status}
          </span>
        </td>
        <td className={`px-4 py-3 text-sm font-bold ${urgencyColors[opportunity.urgency as keyof typeof urgencyColors]}`}>
          {opportunity.urgency === 'high' ? '🔴' : opportunity.urgency === 'medium' ? '🟠' : '🟡'}
        </td>
        <td className="px-4 py-3 text-center">
          <button
            className="text-lg"
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </td>
      </tr>

      {isExpanded && (
        <tr className="bg-gray-50 border-b">
          <td colSpan={7} className="px-4 py-4">
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-gray-600 mb-1">Descripción</p>
                <p className="text-sm text-gray-700">
                  {opportunity.description || 'Sin descripción'}
                </p>
              </div>

              <div className="flex gap-2">
                <select
                  disabled={isLoading}
                  onChange={(e) => handleStateChange(e.target.value)}
                  className="px-2 py-1 border border-gray-300 rounded text-xs"
                >
                  <option value="">Cambiar estado</option>
                  <option value="detected">Detectada</option>
                  <option value="reviewed">Revisada</option>
                  <option value="in_crm">En gestión</option>
                  <option value="cerrada">Cerrada</option>
                </select>

                <input
                  type="text"
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Agregar nota..."
                  disabled={isLoading}
                  className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs"
                />

                <button
                  onClick={handleAddNote}
                  disabled={isLoading || !noteText.trim()}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isLoading ? '...' : 'Agregar'}
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
```

- [ ] **Step 3: Create OpportunityCard.tsx**

```typescript
// frontend/app/nacional/components/shared/OpportunityCard.tsx

import { Opportunity } from '../../types'

interface OpportunityCardProps {
  opportunity: Opportunity
  onClick?: () => void
}

const urgencyBadge = {
  high: { bg: 'bg-red-100', text: 'text-red-700', icon: '🔴' },
  medium: { bg: 'bg-orange-100', text: 'text-orange-700', icon: '🟠' },
  low: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: '🟡' },
}

export default function OpportunityCard({
  opportunity,
  onClick,
}: OpportunityCardProps) {
  const badge = urgencyBadge[opportunity.urgency]

  return (
    <div
      onClick={onClick}
      className="p-4 border border-gray-200 rounded-lg bg-white hover:shadow-md cursor-pointer transition"
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-sm text-gray-900 flex-1">
          {opportunity.title}
        </h3>
        <span className={`px-2 py-1 rounded text-xs font-medium ${badge.bg} ${badge.text}`}>
          {badge.icon} {opportunity.urgency === 'high' ? '7d' : opportunity.urgency === 'medium' ? '15d' : '30d'}
        </span>
      </div>

      <p className="text-xs text-gray-600 mb-3">{opportunity.funder_name}</p>

      <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
        <div>
          <span className="font-semibold text-gray-700">Monto:</span>
          <p className="text-gray-600">
            ${(opportunity.amount_max_cop || 0).toLocaleString('es-CO')}
          </p>
        </div>
        <div>
          <span className="font-semibold text-gray-700">Vencimiento:</span>
          <p className="text-gray-600">
            {opportunity.deadline
              ? new Date(opportunity.deadline).toLocaleDateString('es-CO')
              : 'N/A'}
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
          {opportunity.status}
        </span>
        {opportunity.decision === 'go' && (
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
            GO
          </span>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create LoadingState.tsx**

```typescript
// frontend/app/nacional/components/shared/LoadingState.tsx

export default function LoadingState() {
  return (
    <div className="space-y-4 p-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-24 bg-gray-200 rounded animate-pulse" />
      ))}
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/app/nacional/components/shared/
git commit -m "feat(nacional): add shared components (FilterBar, ExpandableRow, OpportunityCard, LoadingState)"
```

---

## Task 5: NacionalSidebar component

**Files:**
- Create: `frontend/app/nacional/components/NacionalSidebar.tsx`

**Goal:** Build sidebar navigation with section links and metrics badges.

- [ ] **Step 1: Create NacionalSidebar.tsx**

```typescript
// frontend/app/nacional/components/NacionalSidebar.tsx

'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { DashboardMetrics } from '../types'

interface NacionalSidebarProps {
  metrics: DashboardMetrics
  alertCount: number
}

export default function NacionalSidebar({
  metrics,
  alertCount,
}: NacionalSidebarProps) {
  const searchParams = useSearchParams()
  const activeSection = searchParams.get('section') || 'radar'

  const sections = [
    {
      id: 'alertas',
      label: 'Alertas',
      badge: alertCount,
      icon: '🔔',
    },
    {
      id: 'radar',
      label: 'Radar',
      badge: metrics.detected,
      icon: '📊',
    },
    {
      id: 'pipeline',
      label: 'Pipeline',
      badge: metrics.in_crm,
      icon: '📋',
    },
    {
      id: 'contactos',
      label: 'Contactos',
      badge: 0, // TODO: fetch contact count
      icon: '👥',
    },
  ]

  return (
    <aside className="w-64 bg-gray-900 text-white p-6 h-screen overflow-y-auto">
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-2">Nacional Colombia</h2>
        <p className="text-xs text-gray-400">Prospección Estratégica</p>
      </div>

      <nav className="space-y-2">
        {sections.map((section) => (
          <Link
            key={section.id}
            href={`/nacional?section=${section.id}`}
            className={`flex items-center justify-between px-4 py-3 rounded-lg transition ${
              activeSection === section.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-lg">{section.icon}</span>
              <span className="font-medium">{section.label}</span>
            </div>
            {section.badge > 0 && (
              <span className="inline-flex items-center justify-center w-6 h-6 bg-red-600 text-white text-xs font-bold rounded-full">
                {section.badge}
              </span>
            )}
          </Link>
        ))}
      </nav>

      <div className="mt-8 pt-8 border-t border-gray-700">
        <h3 className="text-xs font-semibold text-gray-400 mb-4">RESUMEN</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Detectadas:</span>
            <span className="font-semibold">{metrics.detected}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Revisadas:</span>
            <span className="font-semibold">{metrics.reviewed}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">En gestión:</span>
            <span className="font-semibold">{metrics.in_crm}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Cerradas:</span>
            <span className="font-semibold">{metrics.cerrada}</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/components/NacionalSidebar.tsx
git commit -m "feat(nacional): add NacionalSidebar component with section navigation"
```

---

## Task 6: AlertasSection component

**Files:**
- Create: `frontend/app/nacional/components/AlertasSection.tsx`

**Goal:** Display vencimientos próximos and cambios recientes.

- [ ] **Step 1: Create AlertasSection.tsx**

```typescript
// frontend/app/nacional/components/AlertasSection.tsx

import { Opportunity, Alert } from '../types'
import { generateAlerts } from '../data/nacional-queries'
import OpportunityCard from './shared/OpportunityCard'

interface AlertasSectionProps {
  opportunities: Opportunity[]
}

export default function AlertasSection({
  opportunities,
}: AlertasSectionProps) {
  const alerts = generateAlerts(opportunities)
  const vencimientos = alerts.filter((a) => a.type === 'vencimiento')

  const groupedByUrgency = {
    high: vencimientos.filter((a) => a.urgency === 'high'),
    medium: vencimientos.filter((a) => a.urgency === 'medium'),
    low: vencimientos.filter((a) => a.urgency === 'low'),
  }

  const getOpportunity = (id: string) =>
    opportunities.find((o) => o.id === id)

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Alertas</h1>

      {/* Vencimientos próximos */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Vencimientos próximos
        </h2>

        {vencimientos.length === 0 ? (
          <p className="text-gray-600 text-center py-8">
            No hay alertas de vencimiento
          </p>
        ) : (
          <div className="space-y-6">
            {/* 7 días */}
            {groupedByUrgency.high.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-red-700 mb-3">
                  🔴 Vence en 7 días ({groupedByUrgency.high.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {groupedByUrgency.high.map((alert) => {
                    const opp = getOpportunity(alert.opportunityId)
                    return opp ? (
                      <OpportunityCard
                        key={opp.id}
                        opportunity={opp}
                      />
                    ) : null
                  })}
                </div>
              </div>
            )}

            {/* 15 días */}
            {groupedByUrgency.medium.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-orange-700 mb-3">
                  🟠 Vence en 15 días ({groupedByUrgency.medium.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {groupedByUrgency.medium.map((alert) => {
                    const opp = getOpportunity(alert.opportunityId)
                    return opp ? (
                      <OpportunityCard
                        key={opp.id}
                        opportunity={opp}
                      />
                    ) : null
                  })}
                </div>
              </div>
            )}

            {/* 30 días */}
            {groupedByUrgency.low.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-yellow-700 mb-3">
                  🟡 Vence en 30 días ({groupedByUrgency.low.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {groupedByUrgency.low.map((alert) => {
                    const opp = getOpportunity(alert.opportunityId)
                    return opp ? (
                      <OpportunityCard
                        key={opp.id}
                        opportunity={opp}
                      />
                    ) : null
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Cambios recientes */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Cambios recientes
        </h2>
        <p className="text-gray-600 text-center py-8">
          No hay cambios recientes registrados
        </p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/components/AlertasSection.tsx
git commit -m "feat(nacional): add AlertasSection with vencimientos grouping"
```

---

## Task 7: RadarSection component

**Files:**
- Create: `frontend/app/nacional/components/RadarSection.tsx`

**Goal:** Display overview metrics, distribution chart, and filterable opportunities table.

- [ ] **Step 1: Create RadarSection.tsx**

```typescript
// frontend/app/nacional/components/RadarSection.tsx

'use client'

import { useState } from 'react'
import { Opportunity, FilterState, DashboardMetrics } from '../types'
import FilterBar from './shared/FilterBar'
import ExpandableRow from './shared/ExpandableRow'
import {
  cambiarEstadoOportunidad,
  agregarNotaOportunidad,
} from '../actions/nacional-actions'

interface RadarSectionProps {
  opportunities: Opportunity[]
  metrics: DashboardMetrics
}

export default function RadarSection({
  opportunities,
  metrics,
}: RadarSectionProps) {
  const [filters, setFilters] = useState<FilterState>({
    estado: '',
    urgencia: '',
    financiador: '',
    sector: '',
  })

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  // Extract unique values for filter dropdowns
  const financiadores = [...new Set(opportunities.map((o) => o.funder_name))]
  const sectores = ['Educación privada', 'Tercer sector', 'Gobierno', 'Otros']

  // Apply filters
  const filtered = opportunities.filter((opp) => {
    if (filters.estado && opp.status !== filters.estado) return false
    if (filters.urgencia && opp.urgency !== filters.urgencia) return false
    if (filters.financiador && opp.funder_name !== filters.financiador)
      return false
    if (filters.sector && !opp.description?.includes(filters.sector))
      return false
    return true
  })

  // Distribution by funder
  const byFunder = opportunities.reduce(
    (acc, opp) => {
      acc[opp.funder_name] = (acc[opp.funder_name] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Radar</h1>

      {/* Metrics cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 mb-1">Detectadas</p>
          <p className="text-2xl font-bold text-gray-900">{metrics.detected}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 mb-1">Revisadas</p>
          <p className="text-2xl font-bold text-gray-900">{metrics.reviewed}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 mb-1">En gestión</p>
          <p className="text-2xl font-bold text-gray-900">{metrics.in_crm}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 mb-1">Cerradas</p>
          <p className="text-2xl font-bold text-gray-900">{metrics.cerrada}</p>
        </div>
      </div>

      {/* Distribution by funder */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Distribución por financiador
        </h2>
        <div className="space-y-2">
          {Object.entries(byFunder)
            .sort(([, a], [, b]) => b - a)
            .map(([funder, count]) => (
              <div key={funder} className="flex items-center justify-between">
                <span className="text-sm text-gray-700">{funder}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-200 rounded">
                    <div
                      className="h-full bg-blue-600 rounded"
                      style={{
                        width: `${(count / opportunities.length) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-gray-900 w-8 text-right">
                    {count}
                  </span>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Filters and table */}
      <FilterBar
        activeFilters={filters}
        onFilterChange={handleFilterChange}
        financiadores={financiadores}
        sectores={sectores}
      />

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Oportunidad
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Financiador
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Estado
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Urgencia
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Monto
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Vencimiento
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((opp) => (
              <ExpandableRow
                key={opp.id}
                opportunity={opp}
                onStateChange={(state) =>
                  cambiarEstadoOportunidad(
                    opp.id,
                    state as any
                  )
                }
                onAddNote={(note) =>
                  agregarNotaOportunidad(opp.id, note)
                }
              />
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-8 text-center text-gray-600">
            No hay oportunidades que coincidan con los filtros
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/components/RadarSection.tsx
git commit -m "feat(nacional): add RadarSection with metrics, distribution chart, and filterable table"
```

---

## Task 8: PipelineSection component

**Files:**
- Create: `frontend/app/nacional/components/PipelineSection.tsx`

**Goal:** Display opportunities in active management with expandable details.

- [ ] **Step 1: Create PipelineSection.tsx (similar to Radar but filtered for in_crm status)**

```typescript
// frontend/app/nacional/components/PipelineSection.tsx

'use client'

import { useState } from 'react'
import { Opportunity, FilterState } from '../types'
import FilterBar from './shared/FilterBar'
import ExpandableRow from './shared/ExpandableRow'
import {
  cambiarEstadoOportunidad,
  agregarNotaOportunidad,
} from '../actions/nacional-actions'

interface PipelineSectionProps {
  opportunities: Opportunity[]
}

export default function PipelineSection({
  opportunities,
}: PipelineSectionProps) {
  const [filters, setFilters] = useState<FilterState>({
    estado: 'in_crm',
    urgencia: '',
    financiador: '',
    sector: '',
  })

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const financiadores = [...new Set(opportunities.map((o) => o.funder_name))]
  const sectores = ['Educación privada', 'Tercer sector', 'Gobierno', 'Otros']

  // Only show in_crm and reviewed opportunities
  const pipelineOpps = opportunities.filter(
    (opp) => opp.status === 'in_crm' || opp.status === 'reviewed'
  )

  const filtered = pipelineOpps.filter((opp) => {
    if (filters.estado && opp.status !== filters.estado) return false
    if (filters.urgencia && opp.urgency !== filters.urgencia) return false
    if (filters.financiador && opp.funder_name !== filters.financiador)
      return false
    if (filters.sector && !opp.description?.includes(filters.sector))
      return false
    return true
  })

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Pipeline</h1>

      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <p className="text-sm text-blue-800">
          {filtered.length} oportunidades en gestión activa
        </p>
      </div>

      <FilterBar
        activeFilters={filters}
        onFilterChange={handleFilterChange}
        financiadores={financiadores}
        sectores={sectores}
      />

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Oportunidad
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Financiador
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Monto
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Vencimiento
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Estado
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Urgencia
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                Detalles
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((opp) => (
              <ExpandableRow
                key={opp.id}
                opportunity={opp}
                onStateChange={(state) =>
                  cambiarEstadoOportunidad(opp.id, state as any)
                }
                onAddNote={(note) =>
                  agregarNotaOportunidad(opp.id, note)
                }
              />
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-8 text-center text-gray-600">
            No hay oportunidades en pipeline
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/components/PipelineSection.tsx
git commit -m "feat(nacional): add PipelineSection for active opportunity management"
```

---

## Task 9: ContactosSection component

**Files:**
- Create: `frontend/app/nacional/components/ContactosSection.tsx`

**Goal:** Display contacts grouped by funder with interaction tracking.

- [ ] **Step 1: Create ContactosSection.tsx**

```typescript
// frontend/app/nacional/components/ContactosSection.tsx

'use client'

import { useState } from 'react'
import { Contact, FilterState } from '../types'
import FilterBar from './shared/FilterBar'
import { marcarContactado } from '../actions/nacional-actions'

interface ContactosSectionProps {
  contacts: Contact[]
}

export default function ContactosSection({
  contacts,
}: ContactosSectionProps) {
  const [filters, setFilters] = useState<FilterState>({
    estado: '',
    urgencia: '',
    financiador: '',
    sector: '',
  })

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  // Group contacts by funder
  const byFunder = contacts.reduce(
    (acc, contact) => {
      if (!acc[contact.funder_name]) {
        acc[contact.funder_name] = []
      }
      acc[contact.funder_name].push(contact)
      return acc
    },
    {} as Record<string, Contact[]>
  )

  const financiadores = Object.keys(byFunder)
  const sectores = ['Educación privada', 'Tercer sector', 'Gobierno', 'Otros']

  // Apply funder filter
  const filteredFunders = filters.financiador
    ? { [filters.financiador]: byFunder[filters.financiador] || [] }
    : byFunder

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Contactos</h1>

      <FilterBar
        activeFilters={filters}
        onFilterChange={handleFilterChange}
        financiadores={financiadores}
        sectores={sectores}
      />

      <div className="space-y-6">
        {Object.entries(filteredFunders).map(([funderName, funderContacts]) => (
          <div key={funderName} className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {funderName}
            </h2>

            <div className="space-y-4">
              {funderContacts.map((contact) => (
                <ContactRow
                  key={contact.id}
                  contact={contact}
                  onContactado={marcarContactado}
                />
              ))}
            </div>
          </div>
        ))}

        {Object.keys(filteredFunders).length === 0 && (
          <div className="p-8 text-center text-gray-600">
            No hay contactos para los filtros seleccionados
          </div>
        )}
      </div>
    </div>
  )
}

interface ContactRowProps {
  contact: Contact
  onContactado: (
    id: string,
    type: string,
    note?: string
  ) => Promise<{ success: boolean; error?: string }>
}

function ContactRow({ contact, onContactado }: ContactRowProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [tipoInteraccion, setTipoInteraccion] = useState<'llamada' | 'email' | 'reunion'>('email')

  const handleMarcar = async () => {
    setIsLoading(true)
    try {
      await onContactado(contact.id, tipoInteraccion)
      // Reset form
      setTipoInteraccion('email')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{contact.full_name}</h3>
          <p className="text-sm text-gray-600">{contact.title}</p>
        </div>
        {contact.email_verified && (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✓ Verificado
          </span>
        )}
      </div>

      <div className="mb-3 text-sm">
        <p className="text-gray-700">
          <span className="font-semibold">Email:</span> {contact.email}
        </p>
        {contact.linkedin_url && (
          <p className="text-blue-600 hover:underline">
            <a href={contact.linkedin_url} target="_blank" rel="noopener noreferrer">
              LinkedIn
            </a>
          </p>
        )}
      </div>

      <div className="flex gap-2">
        <select
          disabled={isLoading}
          value={tipoInteraccion}
          onChange={(e) =>
            setTipoInteraccion(e.target.value as 'llamada' | 'email' | 'reunion')
          }
          className="px-2 py-1 border border-gray-300 rounded text-xs"
        >
          <option value="email">Email</option>
          <option value="llamada">Llamada</option>
          <option value="reunion">Reunión</option>
        </select>
        <button
          disabled={isLoading}
          onClick={handleMarcar}
          className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 disabled:bg-gray-400"
        >
          {isLoading ? '...' : 'Marcar contactado'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/components/ContactosSection.tsx
git commit -m "feat(nacional): add ContactosSection with contact management and interaction tracking"
```

---

## Task 10: Main page — nacional/page.tsx

**Files:**
- Modify: `frontend/app/nacional/page.tsx`

**Goal:** Render sidebar + section based on query param, fetch data server-side.

- [ ] **Step 1: Rewrite nacional/page.tsx**

```typescript
// frontend/app/nacional/page.tsx

import { Suspense } from 'react'
import { getOportunidadesNacionales, getDashboardMetrics, getContactosNacionales, generateAlerts } from './data/nacional-queries'
import NacionalSidebar from './components/NacionalSidebar'
import AlertasSection from './components/AlertasSection'
import RadarSection from './components/RadarSection'
import PipelineSection from './components/PipelineSection'
import ContactosSection from './components/ContactosSection'
import LoadingState from './components/shared/LoadingState'
import RunScraperButton from '../components/RunScraperButton'

interface NacionalPageProps {
  searchParams: Promise<{ section?: string }>
}

export default async function NacionalPage({
  searchParams,
}: NacionalPageProps) {
  const params = await searchParams
  const section = params.section || 'radar'

  // Fetch data server-side
  const [opportunities, metrics, contacts] = await Promise.all([
    getOportunidadesNacionales(),
    getDashboardMetrics(),
    getContactosNacionales(),
  ])

  const alerts = generateAlerts(opportunities)
  const alertCount = alerts.length

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <NacionalSidebar metrics={metrics} alertCount={alertCount} />

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar with scraper button */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Nacional Colombia</h1>
          <RunScraperButton
            source="nacional_colombia"
            label="▶ Ejecutar Scraper Nacional"
          />
        </div>

        {/* Section content */}
        <Suspense fallback={<LoadingState />}>
          {section === 'alertas' && (
            <AlertasSection opportunities={opportunities} />
          )}
          {section === 'radar' && (
            <RadarSection opportunities={opportunities} metrics={metrics} />
          )}
          {section === 'pipeline' && (
            <PipelineSection opportunities={opportunities} />
          )}
          {section === 'contactos' && (
            <ContactosSection contacts={contacts} />
          )}
        </Suspense>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/nacional/page.tsx
git commit -m "feat(nacional): refactor main page to render sidebar + dynamic sections"
```

---

## Task 11: Verificación e integración

**Files:**
- Test: Manual verification in browser

**Goal:** Test all 4 sections work end-to-end.

- [ ] **Step 1: Start dev server**

```bash
cd frontend
npm run dev
```

Expected output:
```
   ▲ Next.js 15.3.0
   - Local:        http://localhost:3000
   ✓ Ready in X.Xs
```

- [ ] **Step 2: Navigate to Nacional Colombia**

```
Open browser: http://localhost:3000/nacional
```

Expected:
- Sidebar visible with 4 sections
- "Alertas", "Radar", "Pipeline", "Contactos" clickable
- Badges show counts
- Scraper button visible in top bar

- [ ] **Step 3: Test Alertas section**

Click "Alertas" in sidebar. Verify:
- Page loads without errors
- Shows "Vencimientos próximos" grouped by urgency (7d, 15d, 30d)
- Cards display opportunity title, funder, deadline
- Can click on card to expand details

- [ ] **Step 4: Test Radar section**

Click "Radar". Verify:
- 4 metric cards show (Detectadas, Revisadas, En gestión, Cerradas)
- Bar chart shows distribution by funder
- Table displays opportunities with filters
- Can expand rows to see details and change state
- FilterBar works (state, urgency, financiador filters)

- [ ] **Step 5: Test Pipeline section**

Click "Pipeline". Verify:
- Table shows only in_crm and reviewed opportunities
- Can expand rows and change status
- Can add notes

- [ ] **Step 6: Test Contactos section**

Click "Contactos". Verify:
- Contacts grouped by funder
- Shows name, title, email, verification badge
- Can mark as contacted with interaction type dropdown
- Filter by financiador works

- [ ] **Step 7: Test Scraper button**

Click "▶ Ejecutar Scraper Nacional". Verify:
- Button shows "⏳ Scrapeando..."
- After 10-15 seconds, shows "✓ X nuevas oportunidades"
- Page refreshes to home

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "feat(nacional): complete 4-section nacional colombia page with sidebar, filters, and interactions"
```

---

## Task 12: Documentation

**Files:**
- Create/Update: `docs/nacional-colombia.md` (user guide)

**Goal:** Explain how to use the new Nacional Colombia page.

- [ ] **Step 1: Create user guide**

```markdown
# Nacional Colombia — Guía de Uso

## Visión General

La página Nacional Colombia es un centro de control para la prospección de oportunidades de financiamiento detectadas en fuentes nacionales colombianas.

## Las 4 Secciones

### 1. Alertas 🔔
Muestra vencimientos próximos agrupados por urgencia:
- 🔴 7 días
- 🟠 15 días  
- 🟡 30 días

**Acción:** Haz clic en una tarjeta para expandir y cambiar estado a "Revisada".

### 2. Radar 📊
Panorama completo de oportunidades detectadas:
- **Métricas:** 4 cards con conteos por estado
- **Distribución:** Gráfico de barras por financiador
- **Tabla:** Listado filtrable de todas las oportunidades

**Filtros:** Estado | Urgencia | Financiador | Sector

**Acciones:** Expandir fila → cambiar estado, agregar nota, marcar prioridad

### 3. Pipeline 📋
Oportunidades en gestión activa (estado: Revisada o En gestión).

**Acciones:** Cambiar estado dentro del pipeline, agregar notas de seguimiento.

### 4. Contactos 👥
Red de decisores de financiadores nacionales.

Agrupados por financiador. Para cada contacto:
- Mostrar: nombre, cargo, email, LinkedIn
- Badge verde si email está verificado ✓
- Botón "Marcar contactado" con tipo de interacción (llamada, email, reunión)

## Flujo de Trabajo Sugerido

1. **Lunes:** Revisar Alertas. Cambiar a "Revisada" las que requieren análisis.
2. **Martes-Jueves:** Analizar en Radar. Filtrar por financiador y mover a Pipeline.
3. **Viernes:** Revisar Pipeline. Actualizar estado y próximos pasos.
4. **Permanente:** Contactos. Registrar interacciones con decisores.

## Integración con CRM

Para cada oportunidad en Pipeline ("En gestión"), exporta a tu CRM cuando tengas una propuesta lista.

---

*Última actualización: 26 de mayo de 2026*
```

- [ ] **Step 2: Commit**

```bash
git add docs/nacional-colombia.md
git commit -m "docs(nacional): add user guide for 4-section page"
```

---

## Summary of All Tasks

✅ Task 1: Types (Opportunity, Contact, Alert, FilterState, DashboardMetrics)  
✅ Task 2: Data queries (fetch functions from FastAPI)  
✅ Task 3: Server Actions (cambiarEstado, agregarNota, marcarPrioridad, marcarContactado)  
✅ Task 4: Shared components (FilterBar, ExpandableRow, OpportunityCard, LoadingState)  
✅ Task 5: NacionalSidebar (navigation + metrics)  
✅ Task 6: AlertasSection (vencimientos grouped by urgency)  
✅ Task 7: RadarSection (metrics + chart + filterable table)  
✅ Task 8: PipelineSection (in_crm opportunities with expandables)  
✅ Task 9: ContactosSection (contacts by funder + interaction tracking)  
✅ Task 10: Main page (sidebar + dynamic section rendering)  
✅ Task 11: Verification (end-to-end browser testing)  
✅ Task 12: Documentation (user guide)

---

**Total estimated effort:** 6-8 hours for an experienced developer familiar with Next.js 15 and TypeScript.

**Critical path:** Tasks 1 → 2 → 3 → 4 → 5, then 6-9 in parallel, then 10 → 11 → 12.
